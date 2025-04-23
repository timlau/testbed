import gi

gi.require_version("Gtk", "4.0")
import sys
from random import randint

from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: F401


class PopoverDemo(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id=None, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None
        self.connect("activate", self.on_activate)

    def on_activate(self, application):
        self.window = MainWindow(application=application)
        self.window.set_title("Right-Click Popover Demo")
        self.window.present()


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.set_size_request(440, 250)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(box)

        self.model = Gtk.ListStore(str, str, str, str)
        # Populate some dummy rows
        self.onAddRow(None, None)
        self.onAddRow(None, None)

        self.treeView = Gtk.TreeView(model=self.model)
        self.create_columns()

        self.scrolledWindow = Gtk.ScrolledWindow()
        self.scrolledWindow.set_vexpand(True)
        self.scrolledWindow.set_halign(Gtk.Align.FILL)
        self.scrolledWindow.set_child(self.treeView)
        box.append(self.scrolledWindow)

        clickEvent = Gtk.GestureClick()
        clickEvent.set_button(3)  # Right-click
        clickEvent.connect("pressed", self.onRightMouseClick)
        self.treeView.add_controller(clickEvent)

        action = Gio.SimpleAction.new("add_row", None)
        action.connect("activate", self.onAddRow)
        self.add_action(action)

        menu = Gio.Menu()
        menu.append("Add Row", "win.add_row")

        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(menu)
        self.popover.set_has_arrow(False)
        self.popover.set_parent(self.scrolledWindow)

    def create_columns(self):
        columnNames = ["Column A", "Column A", "Column A", "Column A"]

        for colNum, colName in enumerate(columnNames):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(colName, renderer, text=colNum)

            column.set_fixed_width(108)
            column.set_sort_column_id(colNum)
            self.treeView.append_column(column)

    def onAddRow(self, _widget, _):
        row = [f"{randint(0, 999999)}".zfill(6) for _ in range(4)]
        self.model.append(row)

    def onRightMouseClick(self, _controller, _click_count, x, y):
        rect = Gdk.Rectangle()
        rect.x = x
        rect.y = y
        rect.width = 0
        rect.height = 0
        self.popover.set_pointing_to(rect)

        # # I've also tried this, but the results are no different
        # # --------------------------------------------------------------------
        # pointer = self.treeView.get_display().get_default_seat().get_pointer()
        # surface = pointer.get_surface_at_position()
        # self.popover.set_pointing_to(Gdk.Rectangle(surface.win_x, surface.win_y, 0, 0))

        self.popover.popup()

        return True


app = PopoverDemo()
app.run(sys.argv)
