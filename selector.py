#!/usr/bin/env python3

import argparse
import shlex
from subprocess import PIPE, Popen


class Selector:
    command = ''
    expiration = ''
    videos = None
    files_link = []

    def __init__(self, bucket, camera, expiration):
        self.expiration = expiration
        self.command = 'gsutil ls -l gs://{}/{}/**'.format(bucket, camera)

        self.list_files()
    
    def list_files(self):
        process = Popen(args=shlex.split(self.command), stdout=PIPE)
        stdout, stderr = process.communicate()
        self.videos = stdout.decode('utf-8').split('\n')

    def parse_files(self):
        for v in self.videos:
            information = v.lstrip().rstrip().split('  ')

            if len(information) == 3:
                link = information[2]
                time = information[1]

                if self.is_expired(time):
                    self.files_link.append(link)

        print(len(self.files_link), end='\t')
        print(*self.files_link, sep='\n')

    def is_expired(self, t):
        if t < self.expiration:
            return True

    def reset(self):
        self.command = ''
        self.expiration = ''
        self.videos = None
        del self.files_link[:]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='a subscript to generate output for gsutil')
    parser.add_argument('bucket', action='store')
    parser.add_argument('camera', action='store')
    parser.add_argument('expiration', action='store')
    args = parser.parse_args()

    selector = Selector(bucket=args.bucket, camera=args.camera, expiration=args.expiration)
    selector.parse_files()
    selector.reset()
