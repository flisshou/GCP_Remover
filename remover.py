#!/usr/bin/env python3

import time
import logging
import threading
import shlex
import subprocess
import argparse
from queue import Queue
from threading import Thread
from subprocess import PIPE, Popen
from datetime import datetime
from logging import DEBUG


class RemoverThread(Thread):
    remove_lock = threading.Lock()
    remove_queue = None

    camera = ''
    current_thread = None

    def __init__(self, remove_queue):
        super().__init__()
        self.remove_queue = remove_queue

    def run(self):
        while True:
            try:
                with self.remove_lock:
                    self.camera = self.remove_queue.get()
                    self.current_thread = threading.current_thread().name
                    logging.info('Working on {}'.format(self.camera))
                    print('{} grabbed {} to work'.format(self.current_thread, self.camera))
                self.work()
            finally:
                self.remove_queue.task_done()
                logging.info('Finished working on {}'.format(self.camera))
                print('{} finished working on {}'.format(self.current_thread, self.camera))
    
    def work(self):
        pre_work = self.pre_work().encode('utf-8')
        command = 'gsutil -m rm -I'
        # command = 'grep .mp4'
        process = Popen(args=shlex.split(command), stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate(input=pre_work)
        message = stdout.decode('utf-8')
        err = stderr.decode('utf-8')
        logging.debug(message)
        logging.debug('*gsutil* {}'.format(err))

    def pre_work(self):
        global file_counter
        command = './selector.py {} {} {}'.format(args.bucket, self.camera, args.expiration)
        process = Popen(args=shlex.split(command), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        content = stdout.decode('utf-8').split('\t')

        logging.info('File Amount = {}'.format(content[0]))
        file_counter += int(content[0])

        return content[1]


def check_expiration():
    try:
        datetime.strptime(args.expiration, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        raise ValueError('Incorrect data format. Should be YYYY-mm-ddTHH:MM:SSZ')


def get_camera_list():
    cameras = []
    command = 'gsutil ls gs://{}'.format(args.bucket)
    process = Popen(args=shlex.split(command), stdout=PIPE)
    stdout, stderr = process.communicate()
    subdirectories = stdout.decode('utf-8').split('\n')

    for s in subdirectories:
        if s is not '':
            s = s.split('\n')[0].rstrip('/').split('/')[-1]
            cameras.append(s)

    return cameras


def main():
    camera_list = get_camera_list()
    remove_queue = Queue()

    for t in range(args.t):
        remover = RemoverThread(remove_queue=remove_queue)
        remover.daemon = True
        remover.start()

    for camera in camera_list:
        remove_queue.put(camera)
    remove_queue.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='a script to delete old videos')
    parser.add_argument('bucket', action='store', help='bucket to delete')
    parser.add_argument('expiration', action='store', help='ISO format <YYYY-mm-ddTHH:MM:SSZ>')
    parser.add_argument('-t', action='store', type=int, default=3, help='thread count')
    args = parser.parse_args()

    check_expiration()

    logging.basicConfig(filename='remover.log',level=DEBUG,format='[%(levelname)5s] @ %(asctime)s (%(threadName)-12s) %(message)s')
    logging.info('\n====================================================LOG STARTS====================================================\n'
                 'Target Bucket: {}\n'
                 'Expiration Time Point: {} (Delete Files Before This Time)\n'
                 .format(args.bucket, args.expiration))

    # initialization
    file_counter = 0
    subprocess.run(shlex.split('chmod +x ./selector.py'), stdout=PIPE, stderr=PIPE)
    start = time.time()

    # run threads
    main()

    # result calculations
    end = time.time()
    duration = end - start
    speed = float(file_counter) / duration

    logging.info('\n=====================================================RESULTS======================================================\n'
                 'Total Files = {}\t\tTotal Time = {:04.4f} (sec)\tAvg. Speed = {:04.4f} (file/sec)\n'
                 'Used Thread(s) = {}\n'
                 .format(file_counter, duration, speed, args.t))
    print('[DONE] Spent {:04.4f} seconds; Speed {:04.4f} (file/sec)\nProcessed {} Files.'
          .format(duration, speed, file_counter))
