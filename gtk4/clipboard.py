from cProfile import label
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GObject  # noqa


def on_activate(app):
    global label
    win = Gtk.ApplicationWindow(
        application=app,
        title="Gtk4 is Awesome !!!",
        default_height=400,
        default_width=400,
    )
    box = Gtk.Box()
    box.set_orientation(Gtk.Orientation.VERTICAL)
    label = Gtk.Label()
    label.props.margin_top = 10
    label.props.margin_start = 10
    label.props.xalign = 0
    label.props.yalign = 0
    label.props.vexpand = True
    label.props.hexpand = True
    button = Gtk.Button()
    button.set_label("Get Clipboard")
    button.connect("clicked", on_botton)
    button.hexpand = False
    box.append(label)
    box.append(button)
    win.set_child(box)
    win.present()


def on_botton(widget, *args):
    global label
    read_clipboard(widget)


def read_clipboard(widget):
    global label

    def callback(obj, res, *args):
        text = clb.read_text_finish(res)
        print(f"read text: {text}")
        label.set_text(text)

    clb = widget.get_clipboard()
    clb.read_text_async(None, callback)


def main():
    app = Gtk.Application(application_id="org.gtk.Example")
    app.connect("activate", on_activate)
    app.run(None)


if __name__ == "__main__":
    main()
