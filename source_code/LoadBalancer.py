import bisect
import hashlib
import random
import threading
import time
from collections import deque
from typing import Dict, List, Optional


class Server:
    '''Represents an individual backend application server or container managed by the load balancer'''
    def __init__(self, id: str, addr: str, weight: int = 1):
        self.id = id
        self.weight = weight  # Relative capacity of server
        self.addr = addr  # Network Location
        self.active_conn = 0  # A live counter tracking how many requests are currently being processed on this specific node
        self.total_requests = 0 # Historical counter of all requests ever routed to this node
        self.healthy = True # Boolean flag indicating whether the server is fit to receive traffic
        self.lock = threading.Lock() # A threading.Lock dedicated to protecting mutable state within this instance

    def acquire(self):
        with self.lock:  # Preventing Race Conditions
            self.active_conn += 1
            self.total_requests += 1

    def release(self):
        with self.lock:
            if self.active_conn > 0:
                self.active_conn -= 1

    # Health Check Methods
    # ----------------------
    def mark_unhealthy(self):
        with self.lock:
            self.healthy = False

    def mark_healthy(self):
        with self.lock:
            self.healthy = True
    # ----------------------
    
    def snapshot(self) -> dict:
        with self.lock:
            return {
                'id': self.id,
                'addr': self.addr,
                'weight': self.weight,
                'active_conn': self.active_conn,
                'total_reqs': self.total_requests,
                'healthy': self.healthy,
            }


class ConsistentHashRing:
    """Implements a consistent hash ring with virtual nodes."""
    def __init__(self, replicas_per_weight: int = 50):
        self.replicas_per_weight = replicas_per_weight # Number of virtual points placed on the ring for every 1 unit of server weight
        self.ring: List[int] = []  # Sorted hash keys , A sorted list of 32-bit integers representing points on the ring.
        self.vnode_to_server: Dict[int, str] = {}  # Hash key -> Server ID

    def _hash(self, key: str) -> int:
        '''Converts any string key into a 32-bit integer by taking the MD5 digest of the string and bitwise-ANDing with 0xFFFFFFFF'''
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16) & 0xFFFFFFFF

    def rebuild(self, servers: List[Server]):
        '''Clears existing data, generates virtual node tokens for every healthy server (e.g., srv-1#vnode_0, srv-1#vnode_1), calculates their hash, registers them in vnode_to_server, and sorts self.ring'''
        self.ring.clear()
        self.vnode_to_server.clear()

        for server in servers:
            if not server.healthy:
                continue
            total_vnodes = server.weight * self.replicas_per_weight
            for i in range(total_vnodes):
                vnode_key = f"{server.id}#vnode_{i}"
                h = self._hash(vnode_key)
                self.ring.append(h)
                self.vnode_to_server[h] = server.id

        self.ring.sort()

    def get_server_id(self, routing_key: str) -> Optional[str]:
        '''Hashes the routing_key to get an integer $h$, then performs a binary search using bisect.bisect_right(self.ring, h) to locate the closest virtual node in a clockwise direction. If $h$ is greater than all points on the ring, it wraps around to index 0'''
        if not self.ring:
            return None

        h = self._hash(routing_key)
        # Find the first vnode clockwise
        idx = bisect.bisect_right(self.ring, h)
        if idx == len(self.ring):
            idx = 0  # Wrap around the ring

        return self.vnode_to_server[self.ring[idx]]


class LoadBalancer:
    '''The central coordinator managing server registry, algorithm execution, session state, routing, and background health checks'''
    def __init__(self, algorithm: str = 'round_robin', session_ttl: float = 300.0):
        self.servers: Dict[str, Server] = {}
        self.lock = threading.Lock()
        self.algorithm = algorithm
        self.rr_index = 0
        self.weighted_queue: deque = deque()
        
        # Consistent Hashing & Session Tracking
        self.hash_ring = ConsistentHashRing(replicas_per_weight=50)
        self.sessions: Dict[str, dict] = {}  # session_key -> {'server_id': ..., 'expires_at': ...}
        self.session_ttl = session_ttl  # Time-to-live (in seconds) for sticky sessions

    def add_server(self, server: Server):
        with self.lock:
            self.servers[server.id] = server
            self._sync_topology()

    def remove_server(self, server_id: str):
        with self.lock:
            if server_id in self.servers:
                del self.servers[server_id]
                self._sync_topology()

    def _sync_topology(self):
        """Reconstructs both self.weighted_queue and self.hash_ring based on the current set of healthy servers"""
        # 1. Rebuild weighted queue
        self.weighted_queue.clear()
        for s in self.servers.values():
            if s.healthy:
                cap = min(s.weight, 10)
                for _ in range(cap):
                    self.weighted_queue.append(s.id)

        # 2. Rebuild hash ring
        self.hash_ring.rebuild(list(self.servers.values()))

    def set_algorithm(self, algo: str):
        with self.lock:
            self.algorithm = algo
            self.rr_index = 0

    def _get_healthy_servers_list(self) -> List[Server]:
        return [s for s in self.servers.values() if s.healthy]

    def _resolve_sticky_session(self, session_key: str, healthy_servers: List[Server]) -> Optional[Server]:
        '''Checks if session_key exists in self.sessions and has not expired (expires_at > time.time()).'''
        now = time.time()
        session = self.sessions.get(session_key)

        if session and session['expires_at'] > now:
            server = self.servers.get(session['server_id'])
            if server and server.healthy:
                session['expires_at'] = now + self.session_ttl
                return server

        # Server down or session expired: fallback to hash ring or round robin
        target_id = self.hash_ring.get_server_id(session_key)
        target_server = self.servers.get(target_id) if target_id else None

        if not target_server and healthy_servers:
            target_server = healthy_servers[0]

        if target_server:
            self.sessions[session_key] = {
                'server_id': target_server.id,
                'expires_at': now + self.session_ttl
            }

        return target_server

    def select_server(self, session_key: Optional[str] = None) -> Optional[Server]:
        with self.lock:
            healthy = self._get_healthy_servers_list()
            if not healthy:
                return None

            # 1. Sticky Sessions mode
            if self.algorithm == 'sticky_session':
                if not session_key:
                    # Fallback to round robin if no session key provided
                    idx = self.rr_index % len(healthy)
                    self.rr_index += 1
                    return healthy[idx]
                return self._resolve_sticky_session(session_key, healthy)

            # 2. Consistent Hashing mode
            elif self.algorithm == 'consistent_hashing':
                key = session_key or str(random.random())
                sid = self.hash_ring.get_server_id(key)
                return self.servers.get(sid)

            # 3. Round Robin
            elif self.algorithm == 'round_robin':
                idx = self.rr_index % len(healthy)
                self.rr_index += 1
                return healthy[idx]

            # 4. Weighted Round Robin
            elif self.algorithm == 'weighted_round_robin':
                if not self.weighted_queue:
                    self._sync_topology()
                if not self.weighted_queue:
                    return None
                sid = self.weighted_queue[0]
                self.weighted_queue.rotate(-1)
                return self.servers.get(sid)

            # 5. Least Connection
            elif self.algorithm == 'least_connection':
                return min(healthy, key=lambda s: s.active_conn)

            else:
                return random.choice(healthy)

    def route_request(self, request_id: int, session_key: Optional[str] = None, duration: Optional[float] = None) -> bool:
        server = self.select_server(session_key=session_key)
        if not server:
            print(f'[LB] No healthy servers available for request {request_id}')
            return False

        server.acquire()
        key_log = f" (key: {session_key})" if session_key else ""
        print(f'[LB] Routed req {request_id}{key_log} -> {server.id} (active = {server.active_conn})')
        
        t = threading.Thread(target=self._handle_request, args=(server, request_id, duration))
        t.daemon = True
        t.start()
        return True

    def _handle_request(self, server: Server, request_id: int, duration: Optional[float]):
        '''Simulates request processing via time.sleep(duration) and guarantees cleanup by calling server.release()'''
        if duration is None:
            duration = random.uniform(0.1, 0.4)
        time.sleep(duration)
        server.release()
        print(f'[Server - {server.id}] Finished req {request_id} (active = {server.active_conn})')

    def health_check_cycle(self):
        '''An infinite loop running in the background. Every 2 seconds, it iterates over all servers and simulates random failures (5% chance) and recoveries (30% chance). If any state changes, it calls _sync_topology()'''
        while True:
            with self.lock:
                servers = list(self.servers.values())

            state_changed = False
            for s in servers:
                if s.healthy and random.random() < 0.05:
                    s.mark_unhealthy()
                    state_changed = True
                    print(f'[Health] Server {s.id} marked UNHEALTHY')
                elif not s.healthy and random.random() < 0.3:
                    s.mark_healthy()
                    state_changed = True
                    print(f'[Health] Server {s.id} marked HEALTHY')

            if state_changed:
                with self.lock:
                    self._sync_topology()

            time.sleep(2.0)
            
### Testing Of LoadBalancer System            
            
if __name__ == '__main__':
    lb = LoadBalancer(algorithm='consistent_hashing')

    # Add 3 backend servers with different weights
    lb.add_server(Server('srv-1', '10.0.0.1', weight=1))
    lb.add_server(Server('srv-2', '10.0.0.2', weight=2))
    lb.add_server(Server('srv-3', '10.0.0.3', weight=1))

    # Test Consistent Hashing with specific client session IDs
    clients = ['client_alpha', 'client_beta', 'client_gamma', 'client_alpha', 'client_beta']
    print("--- Testing Consistent Hashing ---")
    for i, client in enumerate(clients):
        lb.route_request(request_id=i + 1, session_key=client, duration=0.2)
        time.sleep(0.05)

    time.sleep(0.5)

    # Test Sticky Sessions
    print("\n--- Testing Sticky Sessions with Server Failure ---")
    lb.set_algorithm('sticky_session')
    
    # Route initial requests
    lb.route_request(request_id=101, session_key='user_100')
    lb.route_request(request_id=102, session_key='user_100')

    # Simulate killing the server user_100 was pinned to
    time.sleep(0.3)
    pinned_sid = lb.sessions['user_100']['server_id']
    lb.servers[pinned_sid].mark_unhealthy()
    with lb.lock:
        lb._sync_topology()

    # Next request for user_100 gracefully fails over
    lb.route_request(request_id=103, session_key='user_100')

    time.sleep(1.0)