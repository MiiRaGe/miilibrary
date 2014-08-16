import platform
import os
import time

import miinaslibrary
import settings
import tools

try:
    import pyinotify
    from pyinotify import WatchManager, Notifier, ThreadedNotifier, ProcessEvent
    
    #Mask for watched events only write, move and close write
    mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MODIFY | pyinotify.IN_MOVED_TO

    class EventProcessor(ProcessEvent):
    
        def process_IN_CLOSE_WRITE(self, event):
            print "Written: %s" % os.path.join(event.path, event.name)
    
        def process_IN_MODIFY(self, event):
            #Doesn't print anything in order to avoid flooding as the event is repeatedly created
            pass
    
        def process_IN_MOVED_TO(self, event):
            print "Moved: %s" % os.path.join(event.path, event.name)
    
    def main_linux():
        wm = WatchManager()
        notifier = Notifier(wm, EventProcessor())
        wm.add_watch(settings.SOURCE_FOLDER, mask, rec=True)
        print('Watching : %s' % settings.SOURCE_FOLDER)
        while True:  # loop forever
            try:
                # process the queue of events as explained above
                notifier.process_events()
                if notifier.check_events(10000):
                    # read notified events and enqeue them
                    notifier.read_events()
                else:
                    print 'Moving, Copying done running mynaslibrary'
                    miinaslibrary.miinaslibrary()
                    print 'Now waiting'
                    notifier.check_events()
            except KeyboardInterrupt:
                # destroy the inotify's instance on this interrupt (stop monitoring)
                print 'Something is wrong, deamon exiting'
                notifier.stop()
                break
        return
except ImportError:
    print("Can't find module inotify, defaulting to Xhours wait")

    def main_linux():
        main_wait()


def main_wait():
    while True:
        miinaslibrary.miinaslibrary()
        time.sleep(3600*4)

if __name__ == '__main__':
    if tools.validate_settings():
        system = platform.system()
        print("Platform is :" + system)
        if system == 'Linux':
            main_linux()
        else:
            main_wait()
    else:
        print "Invalid settings in settings/base.py or settings/local.py"
