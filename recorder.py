import os
import datetime

class Recorder:
    def __init__(self, dir_path):
        
        self.directory_path = os.path.realpath(dir_path)
        os.makedirs(self.directory_path, exist_ok=True)
        self._open_file()

    def _open_file(self):
        self.cur_date = datetime.datetime.today().date()
        file_name = self.cur_date.strftime("%Y-%m-%d")+'.txt'
        self.f = open(os.path.join(self.directory_path, file_name), 'a+')

    def write(self, message, type):
        date = datetime.datetime.today().date()
        if date != self.cur_date:
            self.f.close()
            self._open_file()       

        self.f.write('['+type+']'+message+ '\n')
        self.f.flush()
        



if __name__ == "__main__":

    r = Recorder(config.LOG_PATH)
    r.write('hello','reconnect')

            