import subprocess

cmd = [
    'youtube-dl',
    '--output', 'sounds/%(title)s.%(ext)s',
    '--extract-audio', '--audio-format' ,
    'mp3'
]

print('Enter URL:\r')
input = input()
urlList = input.split(' ')
print('\rDownloading:\n{}\n'.format(urlList))
for url in urlList:
    cmd.append(url)

subprocess.Popen(cmd).wait()
print('\nDownloaded and moved to sounds directory')
