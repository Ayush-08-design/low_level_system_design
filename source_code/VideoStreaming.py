from threading import Thread
import time

class Movie:
    def __init__(self , title , genre , duration):
        self.title = title
        self.genre = genre
        self.duration = duration

class MovieFactory:
    @staticmethod
    def create_movie(title , genre , duration):
        return Movie(title , genre , duration)
        
class StreamingServer:
    __instance = None

    def __init__(self):
        if StreamingServer.__instance is not None:
            raise Exception("Use get_instance() to get access")
        self.catalog = []
        self.users = {}
        StreamingServer.__instance = self

    @staticmethod
    def get_instance():
        if StreamingServer.__instance is None:
            StreamingServer()
        return StreamingServer.__instance
    
    def upload_movie(self , movie : Movie):
        print(f'Uploading Movie {movie.title}')
        time.sleep(1)
        self.catalog.append(movie)
        print(f'Uploaded : {movie.title}')
        
    def remove_movie(self , movie_name):
        self.catalog = [m for m in self.catalog if m.name != movie_name]
        print(f'Removed : {movie_name}')
        
    def search_movie(self , keyword):
        return [m for m in self.catalog if keyword.lower() in m.title.lower()]
    
class Playback:
    def __init__(self , movie):
        self.movie = movie
        self.status = 'Stopped'
        
    def play(self):
        self.status = 'Playing'
        print(f'Now playing : {self.movie.title}')
        time.sleep(1)
        
    def pause(self):
        self.status = 'Paused'
        print(f'Paused : {self.movie.title}')
        
    def stop(self):
        self.status = 'Stopped'
        print(f'Stopped : {self.movie.title}')
        
class User:
    def __init__(self , username):
        self.username = username
        self.history = []
        
    def watch(self , movie):
        playback = Playback(movie)
        playback_thread = Thread(target = playback.play)
        playback_thread.start()
        playback_thread.join()
        self.history.append(movie.title)
        
if __name__ == '__main__':
    print(f'Movie streaming demo')
    
    server = StreamingServer().get_instance()
    
    m1 = MovieFactory.create_movie('Inception' , 'sci-fi' , 148)
    m2 = MovieFactory.create_movie('Intersteller' , 'sci-fi' , 160)
    m3 = MovieFactory.create_movie('The dark knight' , 'Action' , 248)
    
    server.upload_movie(m1)
    server.upload_movie(m2)
    server.upload_movie(m3)
    
    user = User('Dracula')
    
    results = server.search_movie('Inception')
    
    if results:
        user.watch(results[0])
        
    print('User playback history' , user.history)