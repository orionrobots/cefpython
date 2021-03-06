# An example of embedding CEF in PyGTK application.

import platform
if platform.architecture()[0] != "32bit":
    raise Exception("Only 32bit architecture is supported")

import os, sys
libcef_dll = os.path.join(os.path.dirname(os.path.abspath(__file__)),
        'libcef.dll')
if os.path.exists(libcef_dll):
    # Import the local module.
    if 0x02070000 <= sys.hexversion < 0x03000000:
        import cefpython_py27 as cefpython
    elif 0x03000000 <= sys.hexversion < 0x04000000:
        import cefpython_py32 as cefpython
    else:
        raise Exception("Unsupported python version: %s" % sys.version)
else:
    # Import the package.
    from cefpython1 import cefpython

import pygtk
pygtk.require('2.0')
import gtk
import gobject

def GetApplicationPath(file=None):
    import re, os
    # If file is None return current directory without trailing slash.
    if file is None:
        file = ""
    # Only when relative path.
    if not file.startswith("/") and not file.startswith("\\") and (
            not re.search(r"^[\w-]+:", file)):
        if hasattr(sys, "frozen"):
            path = os.path.dirname(sys.executable)
        elif "__file__" in globals():
            path = os.path.dirname(os.path.realpath(__file__))
        else:
            path = os.getcwd()
        path = path + os.sep + file
        path = re.sub(r"[/\\]+", re.escape(os.sep), path)
        path = re.sub(r"[/\\]+$", "", path)
        return path
    return str(file)

def ExceptHook(excType, excValue, traceObject):
    import traceback, os, time, codecs
    # This hook does the following: in case of exception write it to
    # the "error.log" file, display it to the console, shutdown CEF
    # and exit application immediately by ignoring "finally" (_exit()).
    errorMsg = "\n".join(traceback.format_exception(excType, excValue,
            traceObject))
    errorFile = GetApplicationPath("error.log")
    try:
        appEncoding = cefpython.g_applicationSettings["string_encoding"]
    except:
        appEncoding = "utf-8"
    if type(errorMsg) == bytes:
        errorMsg = errorMsg.decode(encoding=appEncoding, errors="replace")
    try:
        with codecs.open(errorFile, mode="a", encoding=appEncoding) as fp:
            fp.write("\n[%s] %s\n" % (
                    time.strftime("%Y-%m-%d %H:%M:%S"), errorMsg))
    except:
        print("cefpython: WARNING: failed writing to error file: %s" % (
                errorFile))
    # Convert error message to ascii before printing, otherwise
    # you may get error like this:
    # | UnicodeEncodeError: 'charmap' codec can't encode characters
    errorMsg = errorMsg.encode("ascii", errors="replace")
    errorMsg = errorMsg.decode("ascii", errors="replace")
    print("\n"+errorMsg+"\n")
    cefpython.QuitMessageLoop()
    cefpython.Shutdown()
    os._exit(1)

class PyGTKExample:

    mainWindow = None
    container = None
    browser = None
    exiting = None
    searchEntry = None

    def __init__(self):

        gobject.timeout_add(10, self.OnTimer)

        self.mainWindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.mainWindow.connect('destroy', self.OnExit)
        self.mainWindow.set_size_request(width=600, height=400)
        self.mainWindow.set_title('PyGTK CEF example')
        self.mainWindow.realize()

        self.container = gtk.DrawingArea()
        self.container.set_property('can-focus', True)
        self.container.connect('size-allocate', self.OnSize)
        self.container.show()

        self.searchEntry = gtk.Entry()
        # By default, clicking a GTK widget doesn't grab the focus away from a native Win32 control (browser).
        self.searchEntry.connect('button-press-event', self.OnWidgetClick)
        self.searchEntry.show()

        table = gtk.Table(3, 1, homogeneous=False)
        self.mainWindow.add(table)
        table.attach(self.CreateMenu(), 0, 1, 0, 1, yoptions=gtk.SHRINK)
        table.attach(self.searchEntry, 0, 1, 1, 2, yoptions=gtk.SHRINK)
        table.attach(self.container, 0, 1, 2, 3)
        table.show()

        windowID = self.container.get_window().handle
        windowInfo = cefpython.WindowInfo()
        windowInfo.SetAsChild(windowID)
        self.browser = cefpython.CreateBrowserSync(windowInfo,
            browserSettings={},
            navigateUrl=GetApplicationPath("cefsimple.html"))

        self.mainWindow.show()

        # Browser took focus, we need to get it back and give to searchEntry.
        self.mainWindow.get_window().focus()
        self.searchEntry.grab_focus()

    def CreateMenu(self):

        file = gtk.MenuItem('File')
        file.show()
        filemenu = gtk.Menu()
        item = gtk.MenuItem('Open')
        filemenu.append(item)
        item.show()
        item = gtk.MenuItem('Exit')
        filemenu.append(item)
        item.show()
        file.set_submenu(filemenu)

        about = gtk.MenuItem('About')
        about.show()

        menubar = gtk.MenuBar()
        menubar.append(file)
        menubar.append(about)
        menubar.show()

        return menubar

    def OnWidgetClick(self, widget, data):

        self.mainWindow.get_window().focus()

    def OnTimer(self):

        if self.exiting:
            return False
        cefpython.MessageLoopWork()
        return True

    def OnFocusIn(self, widget, data):

        # This function is currently not called by any of code, but if you would like
        # for browser to have automatic focus add such line:
        # self.mainWindow.connect('focus-in-event', self.OnFocusIn)
        cefpython.WindowUtils.OnSetFocus(self.container.get_window().handle, 0, 0, 0)

    def OnSize(self, widget, sizeAlloc):

        cefpython.WindowUtils.OnSize(self.container.get_window().handle, 0, 0, 0)

    def OnExit(self, widget, data=None):

        self.exiting = True
        gtk.main_quit()

if __name__ == '__main__':

    version = '.'.join(map(str, list(gtk.gtk_version)))
    print('GTK version: %s' % version)

    sys.excepthook = ExceptHook
    settings = {
        "log_severity": cefpython.LOGSEVERITY_INFO,
        "log_file": GetApplicationPath("debug.log"),
        "release_dcheck_enabled": True # Enable only when debugging.
    }
    cefpython.Initialize(settings)

    gobject.threads_init() # timer for messageloop
    PyGTKExample()
    gtk.main()

    cefpython.Shutdown()
