"""Set window properties with Xlib (from Qt)."""

__all__ = ['ALL_DESKTOPS', 'move_to_desktop', 'set_empty_window_shape']

from cffi import FFI
import sip

CDEF = """
typedef unsigned long XID;
typedef XID Window;
typedef unsigned long Atom;
typedef int Bool;
typedef char *XPointer;
typedef unsigned long VisualID;
typedef int Status;
typedef XID GContext;
typedef XID Colormap;
typedef XID XserverRegion;

typedef ... XExtData;
typedef ... _XPrivate;
typedef ... Depth;
typedef ... Visual;

typedef struct {
        XExtData *ext_data;     /* hook for extension to hang data */
        int depth;              /* depth of this image format */
        int bits_per_pixel;     /* bits/pixel at this depth */
        int scanline_pad;       /* scanline must padded to this multiple */
} ScreenFormat;

typedef struct _XGC
{
    XExtData *ext_data; /* hook for extension to hang data */
    GContext gid;       /* protocol ID for graphics context */
    /* there is more to this structure, but it is private to Xlib */
}
*GC;

struct _XDisplay;

typedef struct {
        XExtData *ext_data;     /* hook for extension to hang data */
        struct _XDisplay *display;/* back pointer to display structure */
        Window root;            /* Root window id. */
        int width, height;      /* width and height of screen */
        int mwidth, mheight;    /* width and height of  in millimeters */
        int ndepths;            /* number of depths possible */
        Depth *depths;          /* list of allowable depths on the screen */
        int root_depth;         /* bits per pixel */
        Visual *root_visual;    /* root visual */
        GC default_gc;          /* GC for the root root visual */
        Colormap cmap;          /* default color map */
        unsigned long white_pixel;
        unsigned long black_pixel;      /* White and Black pixel values */
        int max_maps, min_maps; /* max and min color maps */
        int backing_store;      /* Never, WhenMapped, Always */
        Bool save_unders;
        long root_input_mask;   /* initial root input mask */
} Screen;

typedef struct _XDisplay
{
        XExtData *ext_data;     /* hook for extension to hang data */
        struct _XPrivate *private1;
        int fd;                 /* Network socket. */
        int private2;
        int proto_major_version;/* major version of server's X protocol */
        int proto_minor_version;/* minor version of servers X protocol */
        char *vendor;           /* vendor of the server hardware */
        XID private3;
        XID private4;
        XID private5;
        int private6;
        XID (*resource_alloc)(  /* allocator function */
                struct _XDisplay *
        );
        int byte_order;         /* screen byte order, LSBFirst, MSBFirst */
        int bitmap_unit;        /* padding and data requirements */
        int bitmap_pad;         /* padding requirements on bitmaps */
        int bitmap_bit_order;   /* LeastSignificant or MostSignificant */
        int nformats;           /* number of pixmap formats in list */
        ScreenFormat *pixmap_format;    /* pixmap format list */
        int private8;
        int release;            /* release of the server */
        struct _XPrivate *private9, *private10;
        int qlen;               /* Length of input event queue */
        unsigned long last_request_read; /* seq number of last event read */
        unsigned long request;  /* sequence number of last request. */
        XPointer private11;
        XPointer private12;
        XPointer private13;
        XPointer private14;
        unsigned max_request_size; /* maximum number 32 bit words in request*/
        struct _XrmHashBucketRec *db;
        int (*private15)(
                struct _XDisplay *
                );
        char *display_name;     /* "host:display" string used on this connect*/
        int default_screen;     /* default screen for operations */
        int nscreens;           /* number of screens on this server*/
        Screen *screens;        /* pointer to list of screens */
        unsigned long motion_buffer;    /* size of motion buffer */
        unsigned long private16;
        int min_keycode;        /* minimum defined keycode */
        int max_keycode;        /* maximum defined keycode */
        XPointer private17;
        XPointer private18;
        int private19;
        char *xdefaults;        /* contents of defaults from server */
        /* there is more to this structure, but it is private to Xlib */
}
Display;

typedef struct {
        int type;
        unsigned long serial;   /* # of last request processed by server */
        Bool send_event;        /* true if this came from a SendEvent request */
        Display *display;       /* Display the event was read from */
        Window window;
        Atom message_type;
        int format;
        union {
                char b[20];
                short s[10];
                long l[5];
                } data;
} XClientMessageEvent;

typedef union _XEvent {
        int type;               /* must not be changed; first element */
        XClientMessageEvent xclient;
        long pad[24];
} XEvent;

typedef struct {
    short x, y;
    unsigned short width, height;
} XRectangle;

extern Atom XInternAtom(
    Display*            /* display */,
    const char*         /* atom_name */,
    Bool                /* only_if_exists */
);

extern Status XSendEvent(
    Display*            /* display */,
    Window              /* w */,
    Bool                /* propagate */,
    long                /* event_mask */,
    XEvent*             /* event_send */
);

XserverRegion
XFixesCreateRegion (Display *dpy, XRectangle *rectangles, int nrectangles);

void
XFixesSetWindowShapeRegion (Display *dpy, Window win, int shape_kind,
                            int x_off, int y_off, XserverRegion region);

void
XFixesDestroyRegion (Display *dpy, XserverRegion region);
"""

# Since there are no Xlib functions to access the root window of a display (only macros),
# we need to define XLIB_ILLEGAL_ACCESS so we can access the related fields.
VERIFY = """
#define XLIB_ILLEGAL_ACCESS
#include <X11/Xlib.h>
#include <X11/extensions/shape.h>
#include <X11/extensions/Xfixes.h>
"""

# Other Xlib constants
ClientMessage = 33
SubstructureRedirectMask = (1 << 20)
SubstructureNotifyMask = (1 << 19)
ShapeInput = 2
ALL_DESKTOPS = -1

# Set up C bindings
ffi = FFI()
ffi.cdef(CDEF)
C = ffi.verify(VERIFY, libraries=["X11", "Xfixes"])


def move_to_desktop(display, window_id, desktop):
    """
    Move this window to a numbered desktop.

    To make the window sticky, move it to ALL_DESKTOPS.
    """
    display_ptr = ffi.cast("Display *", sip.unwrapinstance(display))
    root = display_ptr.screens[display_ptr.default_screen].root
    mask = SubstructureRedirectMask | SubstructureNotifyMask

    event = ffi.new("XEvent *")
    event.xclient.type = ClientMessage
    event.xclient.send_event = True
    event.xclient.message_type = C.XInternAtom(display_ptr, b"_NET_WM_DESKTOP", False)
    event.xclient.window = window_id
    event.xclient.format = 32
    event.xclient.data.l[0] = desktop

    C.XSendEvent(display_ptr, root, False, mask, event)


def set_empty_window_shape(display, window_id):
    display_ptr = ffi.cast("Display *", sip.unwrapinstance(display))
    empty = ffi.new("XRectangle *")
    region = C.XFixesCreateRegion(display_ptr, empty, 1)
    C.XFixesSetWindowShapeRegion(display_ptr, window_id, ShapeInput, 0, 0, region)
    C.XFixesDestroyRegion(display_ptr, region)
