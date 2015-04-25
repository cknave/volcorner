"""Minimal ALSA mixer CFFI binding."""

__all__ = [
    "ALSAMixerError",
    "Control",
    "Mixer",
    "SND_MIXER_SCHN_UNKNOWN",
    "SND_MIXER_SCHN_FRONT_LEFT",
    "SND_MIXER_SCHN_FRONT_RIGHT",
    "SND_MIXER_SCHN_REAR_LEFT",
    "SND_MIXER_SCHN_REAR_RIGHT",
    "SND_MIXER_SCHN_FRONT_CENTER",
    "SND_MIXER_SCHN_WOOFER",
    "SND_MIXER_SCHN_SIDE_LEFT",
    "SND_MIXER_SCHN_SIDE_RIGHT",
    "SND_MIXER_SCHN_REAR_CENTER",
    "SND_MIXER_SCHN_LAST",
    "SND_MIXER_SCHN_MONO",
]

from cffi import FFI
import select

CDEF = """
typedef ... snd_mixer_t;
typedef ... snd_mixer_class_t;
typedef ... snd_mixer_selem_id_t;
typedef ... snd_mixer_elem_t;

typedef enum _snd_mixer_selem_channel_id {
 SND_MIXER_SCHN_UNKNOWN = -1,
 SND_MIXER_SCHN_FRONT_LEFT = 0,
 SND_MIXER_SCHN_FRONT_RIGHT,
 SND_MIXER_SCHN_REAR_LEFT,
 SND_MIXER_SCHN_REAR_RIGHT,
 SND_MIXER_SCHN_FRONT_CENTER,
 SND_MIXER_SCHN_WOOFER,
 SND_MIXER_SCHN_SIDE_LEFT,
 SND_MIXER_SCHN_SIDE_RIGHT,
 SND_MIXER_SCHN_REAR_CENTER,
 SND_MIXER_SCHN_LAST = 31,
 SND_MIXER_SCHN_MONO = SND_MIXER_SCHN_FRONT_LEFT
} snd_mixer_selem_channel_id_t;

struct pollfd {
    int   fd;         /* file descriptor */
    short events;     /* requested events */
    short revents;    /* returned events */
};

int snd_mixer_open(snd_mixer_t **mixer, int mode);
int snd_mixer_attach(snd_mixer_t *mixer, const char *name);
int snd_mixer_load(snd_mixer_t *mixer);
int snd_mixer_poll_descriptors_count(snd_mixer_t *mixer);
int snd_mixer_poll_descriptors(snd_mixer_t *mixer, struct pollfd *pfds, unsigned int space);
int snd_mixer_poll_descriptors_revents(snd_mixer_t *mixer, struct pollfd *pfds, unsigned int nfds,
                                       unsigned short *revents);

int snd_mixer_selem_register(snd_mixer_t *mixer,
        struct snd_mixer_selem_regopt *options,
        snd_mixer_class_t **classp);
int snd_mixer_selem_id_malloc(snd_mixer_selem_id_t **ptr);
void snd_mixer_selem_id_free(snd_mixer_selem_id_t *obj);
void snd_mixer_selem_id_set_name(snd_mixer_selem_id_t *obj, const char *val);
snd_mixer_elem_t *snd_mixer_find_selem(snd_mixer_t *mixer,
           const snd_mixer_selem_id_t *id);
int snd_mixer_selem_set_playback_volume(snd_mixer_elem_t *elem, snd_mixer_selem_channel_id_t channel, long value);
int snd_mixer_selem_set_playback_volume_all(snd_mixer_elem_t *elem, long value);
int snd_mixer_selem_get_playback_volume(snd_mixer_elem_t *elem, snd_mixer_selem_channel_id_t channel, long *value);
int snd_mixer_handle_events(snd_mixer_t *mixer);

int snd_mixer_selem_get_playback_dB_range(snd_mixer_elem_t *, long *, long *);
int snd_mixer_selem_get_playback_volume_range(snd_mixer_elem_t *, long *, long *);
int snd_mixer_selem_get_playback_dB(snd_mixer_elem_t *, snd_mixer_selem_channel_id_t, long *);
int snd_mixer_selem_set_playback_dB(snd_mixer_elem_t *, snd_mixer_selem_channel_id_t, long, int);
int snd_mixer_selem_set_playback_dB_all(snd_mixer_elem_t *, long, int);
"""

# Set up C bindings
ffi = FFI()
ffi.cdef(CDEF)
C = ffi.verify("#include <alsa/asoundlib.h>", libraries=["asound"])

# Python version of constants
SND_MIXER_SCHN_UNKNOWN = C.SND_MIXER_SCHN_UNKNOWN
SND_MIXER_SCHN_FRONT_LEFT = C.SND_MIXER_SCHN_FRONT_LEFT
SND_MIXER_SCHN_FRONT_RIGHT = C.SND_MIXER_SCHN_FRONT_RIGHT
SND_MIXER_SCHN_REAR_LEFT = C.SND_MIXER_SCHN_REAR_LEFT
SND_MIXER_SCHN_REAR_RIGHT = C.SND_MIXER_SCHN_REAR_RIGHT
SND_MIXER_SCHN_FRONT_CENTER = C.SND_MIXER_SCHN_FRONT_CENTER
SND_MIXER_SCHN_WOOFER = C.SND_MIXER_SCHN_WOOFER
SND_MIXER_SCHN_SIDE_LEFT = C.SND_MIXER_SCHN_SIDE_LEFT
SND_MIXER_SCHN_SIDE_RIGHT = C.SND_MIXER_SCHN_SIDE_RIGHT
SND_MIXER_SCHN_REAR_CENTER = C.SND_MIXER_SCHN_REAR_CENTER
SND_MIXER_SCHN_LAST = C.SND_MIXER_SCHN_LAST
SND_MIXER_SCHN_MONO = C.SND_MIXER_SCHN_MONO


class Mixer:
    """ALSA mixer."""
    def __init__(self, name="default"):
        """
        Initialize an ALSA mixer.

        :param str name: The ALSA mixer name (e.g. "default", "hw:0")
        """
        self.name = name

        # Open the mixer.
        mixer_ptr = ffi.new("snd_mixer_t **")
        _chk(C.snd_mixer_open(mixer_ptr, 0))
        self.mixer = mixer_ptr[0]

        # Initialize it.
        _chk(C.snd_mixer_attach(self.mixer, _utf8(name)))
        _chk(C.snd_mixer_selem_register(self.mixer, ffi.NULL, ffi.NULL))
        _chk(C.snd_mixer_load(self.mixer))

    def __repr__(self):
        return '<Mixer {}>'.format(repr(self.name))

    def find_control(self, name):
        """
        Find a mixer control.

        :param str name: The Mixer Control name (e.g. "Master, PCM")
        :return: :class:`Control` or None
        """
        # Allocate and initialize an ID.
        id_ptr = ffi.new("snd_mixer_selem_id_t **")
        _chk(C.snd_mixer_selem_id_malloc(id_ptr))
        elem_id = id_ptr[0]
        try:
            C.snd_mixer_selem_id_set_name(elem_id, _utf8(name))

            # Find the control.
            elem = C.snd_mixer_find_selem(self.mixer, elem_id)
            if elem:
                return Control(elem, name)
            else:
                return None
        finally:
            C.snd_mixer_selem_id_free(elem_id)

    def poll(self, breakfd=None, timeout=None):
        """
        Poll for ALSA events on this Mixer.

        :param int breakfd: An additional file descriptor to poll
        :param int timeout: Optional timeout, in milliseconds
        :return: True if an ALSA event was handled, False if breakfd was polled or timed out
        """
        # Prepare the poll object.
        fds = self._get_poll_descriptors()
        poll = self._poll_obj_from_fds(fds)
        if breakfd is not None:
            poll.register(breakfd)

        # Wait for an update.
        results = poll.poll(timeout)

        # Process the update, unless it was the break fd.
        alsa_results = [f for f in results if f[0] != breakfd]
        if len(alsa_results) > 0:
            result_fds = self._fds_from_poll_results(alsa_results)
            revents = ffi.new("unsigned short[1]")
            _chk(C.snd_mixer_poll_descriptors_revents(self.mixer, result_fds, len(alsa_results), revents))
            if revents[0] & (select.POLLERR | select.POLLNVAL):
                raise ALSAMixerError("Mixer read error", revents[0])
            _chk(C.snd_mixer_handle_events(self.mixer))
            return True
        return False

    def _get_poll_descriptors(self):
        """Get a list of pollfd structs for this Mixer."""
        # Get the poll descriptor count
        expected = C.snd_mixer_poll_descriptors_count(self.mixer)
        if expected < 1:
            raise ALSAMixerError("No poll descriptors count", expected)

        # Get the poll descriptors
        fds = ffi.new("struct pollfd[{}]".format(expected))
        count = C.snd_mixer_poll_descriptors(self.mixer, fds, expected)
        if count < 1:
            raise ALSAMixerError("No poll descriptors returned", count)

        return fds[0:count]

    @staticmethod
    def _poll_obj_from_fds(fds):
        """Convert a list of pollfd structs into a :class:`select.poll`."""
        poll_obj = select.poll()
        for pollfd in fds:
            poll_obj.register(pollfd.fd, pollfd.events)
        return poll_obj

    @staticmethod
    def _fds_from_poll_results(results):
        """Convert the results of :meth:`select.poll.poll()` to a list of pollfd structs."""
        fds = ffi.new("struct pollfd[{}]".format(len(results)))
        for i, result in enumerate(results):
            fds[i].fd = result[0]
            fds[i].revents = result[1]
        return fds


class Control:
    """ALSA Mixer Control."""
    def __init__(self, elem, name):
        """Initialize an ALSA mixer control.
        
        :param elem: The mixer element
        :type elem: snd_mixer_elem_t *
        :param str name: The Control name
        """
        self.elem = elem
        self.name = name

    def __repr__(self):
        return "<Control {}>".format(repr(self.name))

    def get_raw_range(self):
        """
        Get the range of this control.

        :return: (min, max) tuple
        """
        min_ptr = ffi.new("long *")
        max_ptr = ffi.new("long *")
        _chk(C.snd_mixer_selem_get_playback_volume_range(self.elem, min_ptr, max_ptr))
        return min_ptr[0], max_ptr[0]

    def get_raw_volume(self, channel=0):
        """
        Get the volume of this control, as of the last Mixer poll.

        :param int channel: The channel number
        :return: The volume
        """
        volume_ptr = ffi.new("long *")
        _chk(C.snd_mixer_selem_get_playback_volume(self.elem, channel, volume_ptr))
        return volume_ptr[0]

    def set_raw_volume(self, volume, channel=None):
        """
        Set the volume of this control.

        :param volume: The new volume
        :param int channel: The channel number

        """
        if channel is None:
            _chk(C.snd_mixer_selem_set_playback_volume_all(self.elem, volume))
        else:
            _chk(C.snd_mixer_selem_set_playback_volume(self.elem, channel, volume))

    def get_db_range(self):
        """
        Get the range of this control in decibels × 100.

        :return: (min, max) tuple
        """
        min_ptr = ffi.new("long *")
        max_ptr = ffi.new("long *")
        _chk(C.snd_mixer_selem_get_playback_dB_range(self.elem, min_ptr, max_ptr))
        return min_ptr[0], max_ptr[0]

    def get_db(self, channel=0):
        """
        Get the volume of this control in decibels × 100, as of the last Mixer poll.

        :param int channel: The channel number
        :return: The volume
        """
        volume_ptr = ffi.new("long *")
        _chk(C.snd_mixer_selem_get_playback_dB(self.elem, channel, volume_ptr))
        return volume_ptr[0]

    def set_db(self, volume, channel=None, dir=0):
        """
        Set the volume of this control in decibels × 100.

        :param volume: The new volume
        :param int channel: The channel number
        :param int dir: Select direction (-1 = accurate or first bellow, 0 = accurate, 1 = accurate or first above)
        """
        if channel is None:
            _chk(C.snd_mixer_selem_set_playback_dB_all(self.elem, volume, dir))
        else:
            _chk(C.snd_mixer_selem_set_playback_dB(self.elem, channel, volume, dir))


class ALSAMixerError(Exception):
    """ALSA mixer error."""
    def __init__(self, message=None, code=None):
        """Instantiate a new mixer error.

        :param message: The error message
        :param code: The error code

        """
        assert (message is not None) or (code is not None)
        self.message = message
        self.code = code


def _chk(rc):
    """Check a return code is OK."""
    if rc < 0:
        raise ALSAMixerError(code=rc)


def _utf8(s):
    """Convert a string to utf-8 bytes."""
    return s.encode("utf-8")
