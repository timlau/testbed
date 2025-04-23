import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gio, GObject, Gtk  # noqa: E402


class DataObject(GObject.GObject):
    def __init__(self, txt: str):
        super(DataObject, self).__init__()
        self.data = txt


class ExampleWindow(Gtk.ApplicationWindow):
    def __init__(self):
        super().__init__()
        self.set_title("ListView with Right-Click Menu")
        self.set_default_size(400, 300)
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect("pressed", self.press)
        gesture.connect("released", self.release)

        # Create a ListStore (data model)
        self.store = Gio.ListStore.new(DataObject)
        self.store.append(DataObject("Item 1"))
        self.store.append(DataObject("Item 2"))
        self.store.append(DataObject("Item 3"))

        # Create a ListView
        self.model = Gtk.SingleSelection.new(self.store)
        self.listview = Gtk.ListView(model=self.model, factory=self.create_factory())
        self.listview.connect("activate", self.on_item_activated)
        self.listview.add_controller(gesture)
        # Add a right-click menu

        # Add the ListView to the window
        self.set_child(self.listview)

    def create_factory(self):
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.on_setup)
        factory.connect("bind", self.on_bind)
        return factory

    def on_setup(self, factory, list_item):
        label = Gtk.Label()
        label.set_xalign(0)
        list_item.set_child(label)

    def on_bind(self, factory, list_item):
        label = list_item.get_child()
        item = list_item.get_item()
        label.set_text(item.data)

    def on_button_press(self, widget, event):
        if event.button == 3:  # Right-click
            # Create a PopoverMenu
            menu = Gtk.PopoverMenu()
            # menu.set_pointing_to(event)
            # menu.set_parent(widget)

            # Create actions for the menu
            action_group = Gio.SimpleActionGroup()
            self.insert_action_group("context", action_group)

            action = Gio.SimpleAction.new("delete", None)
            action.connect("activate", self.on_delete_item)
            action_group.add_action(action)

            # Add menu items
            menu_model = Gio.Menu()
            menu_model.append("Delete", "context.delete")
            menu.set_menu_model(menu_model)

            # Show the menu
            menu.popup()

    def press(self, *args):
        print(f"Pressed : {args}")

    def release(self, _controller, _click_count, x, y):
        print(f"Released : {_click_count} {x} {y}")
        # if n_press == 1:
        #     # Handle single click
        #     print("Single click detected")
        # elif n_press == 2:
        #     # Handle double click
        #     print("Double click detected")
        # Create a PopoverMenu
        menu = Gtk.PopoverMenu()
        rect = Gdk.Rectangle()
        rect.x = x
        rect.y = y
        rect.width = 0
        rect.height = 0
        menu.set_pointing_to(rect)
        menu.set_has_arrow(False)
        menu.set_parent(self.listview)

        # Create actions for the menu
        action_group = Gio.SimpleActionGroup()
        self.insert_action_group("context", action_group)

        action = Gio.SimpleAction.new("delete", None)
        action.connect("activate", self.on_delete_item)
        action_group.add_action(action)

        # Add menu items
        menu_model = Gio.Menu()
        menu_model.append("Delete", "context.delete")
        menu.set_menu_model(menu_model)

        # Show the menu
        menu.popup()

    def on_delete_item(self, action, param):
        print("Delete action triggered")

    def on_item_activated(self, listview, position):
        print(f"Item activated at position {position}")


# Run the application
class ExampleApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.ListViewMenu")

    def do_activate(self):
        win = ExampleWindow()
        win.set_application(self)
        win.show()


app = ExampleApp()
app.run()
