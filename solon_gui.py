#!/usr/bin/env python3
"""
Solon GUI - Native macOS GUI for configuration
"""

import sys
import os
import objc
from AppKit import (
    NSApplication, NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable, NSWindowStyleMaskResizable,
    NSView, NSButton, NSTextField, NSPopUpButton, NSTableView, NSTableColumn,
    NSRect, NSPoint, NSSize, NSMakeRect, NSColor, NSFont, NSFontManager,
    NSAlert, NSInformationalAlertStyle, NSWindowController, NSBox,
    NSStackView, NSLayoutConstraint, NSLayoutAttributeLeading,
    NSLayoutAttributeTrailing, NSLayoutAttributeTop, NSLayoutAttributeBottom,
    NSLayoutRelationEqual, NSLayoutConstraint, NSUserDefaults, NSScrollView
)
from Foundation import NSObject, NSString
from behavior_registry import BehaviorRegistry
from app_launcher import get_apps_with_login_items, is_app_running


class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        pass


class SolonGUI(NSWindowController):
    def init(self):
        # Initialize the window controller
        self = objc.super(SolonGUI, self).init()
        if self is None:
            return None
        
        # Initialize registry
        self.registry = BehaviorRegistry()
        
        # Get available apps
        self.available_apps = self.get_available_apps()
        
        # Create window
        window_rect = NSMakeRect(100, 100, 800, 600)
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | 
            NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable,
            2,  # NSBackingStoreBuffered
            False
        )
        window.setTitle_("Solon Configuration")
        window.setMinSize_(NSSize(600, 400))
        
        # Set the window for the controller
        self.setWindow_(window)
        
        # Initialize data structures before UI setup (needed for data source methods)
        self.startup_apps = []
        self.display_rules = {"w1": [], "w2": [], "laptop": []}
        
        # Setup UI
        self.setup_ui()
        
        # Load current configuration
        self.load_configuration()
        
        return self
    
    def get_available_apps(self):
        """Get list of available applications"""
        apps = []
        applications_dir = "/Applications"
        if os.path.exists(applications_dir):
            for item in os.listdir(applications_dir):
                if item.endswith('.app'):
                    apps.append(item.replace('.app', ''))
        return sorted(apps)
    
    def setup_ui(self):
        """Setup the user interface"""
        content_view = self.window().contentView()
        
        # Create main container
        container = NSView.alloc().initWithFrame_(content_view.bounds())
        container.setAutoresizingMask_(0x12)  # Width and height
        
        # Startup section
        startup_box = self.create_startup_section()
        startup_box.setFrame_(NSMakeRect(20, 400, 760, 150))
        container.addSubview_(startup_box)
        
        # Display rules section
        display_box = self.create_display_rules_section()
        display_box.setFrame_(NSMakeRect(20, 20, 760, 360))
        container.addSubview_(display_box)
        
        # Save button
        save_button = NSButton.alloc().initWithFrame_(NSMakeRect(650, 570, 100, 30))
        save_button.setTitle_("Save")
        save_button.setButtonType_(1)  # NSButtonTypeMomentaryPushIn
        save_button.setTarget_(self)
        save_button.setAction_('saveConfiguration:')
        container.addSubview_(save_button)
        
        content_view.addSubview_(container)
    
    def create_startup_section(self):
        """Create startup apps section"""
        box = NSBox.alloc().initWithFrame_(NSMakeRect(0, 0, 760, 150))
        box.setTitle_("Startup Apps")
        
        content_view = box.contentView()
        
        # Label
        label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 100, 200, 20))
        label.setStringValue_("Apps to keep open on login:")
        label.setBordered_(False)
        label.setDrawsBackground_(False)
        label.setEditable_(False)
        content_view.addSubview_(label)
        
        # App dropdown
        self.startup_app_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(10, 70, 200, 25))
        self.startup_app_popup.addItemsWithTitles_(self.available_apps)
        content_view.addSubview_(self.startup_app_popup)
        
        # Add button
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(220, 70, 60, 25))
        add_button.setTitle_("Add")
        add_button.setButtonType_(1)
        add_button.setTarget_(self)
        add_button.setAction_('addStartupApp:')
        content_view.addSubview_(add_button)
        
        # List view for selected apps
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 10, 300, 50))
        self.startup_table = NSTableView.alloc().init()
        
        column = NSTableColumn.alloc().initWithIdentifier_("app")
        column.setTitle_("App")
        column.setWidth_(280)
        self.startup_table.addTableColumn_(column)
        self.startup_table.setHeaderView_(None)
        self.startup_table.setDataSource_(self)
        self.startup_table.setDelegate_(self)
        
        scroll_view.setDocumentView_(self.startup_table)
        scroll_view.setHasVerticalScroller_(True)
        content_view.addSubview_(scroll_view)
        
        # startup_apps is already initialized in init()
        
        return box
    
    def create_display_rules_section(self):
        """Create display rules section"""
        box = NSBox.alloc().initWithFrame_(NSMakeRect(0, 0, 760, 360))
        box.setTitle_("Display Rules")
        
        content_view = box.contentView()
        
        # Store references to UI elements
        self.display_ui_elements = {}
        
        # W1 section
        w1_box, w1_elements = self.create_display_rule_box("W1 (Display 2)", "w1", NSMakeRect(10, 240, 240, 110))
        content_view.addSubview_(w1_box)
        self.display_ui_elements["w1"] = w1_elements
        
        # W2 section
        w2_box, w2_elements = self.create_display_rule_box("W2 (Display 3)", "w2", NSMakeRect(260, 240, 240, 110))
        content_view.addSubview_(w2_box)
        self.display_ui_elements["w2"] = w2_elements
        
        # Laptop section
        laptop_box, laptop_elements = self.create_display_rule_box("Laptop", "laptop", NSMakeRect(510, 240, 240, 110))
        content_view.addSubview_(laptop_box)
        self.display_ui_elements["laptop"] = laptop_elements
        
        # Rules list
        rules_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 210, 200, 20))
        rules_label.setStringValue_("Configured Rules:")
        rules_label.setBordered_(False)
        rules_label.setDrawsBackground_(False)
        rules_label.setEditable_(False)
        content_view.addSubview_(rules_label)
        
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(10, 10, 740, 190))
        self.rules_table = NSTableView.alloc().init()
        
        app_column = NSTableColumn.alloc().initWithIdentifier_("app")
        app_column.setTitle_("App")
        app_column.setWidth_(200)
        self.rules_table.addTableColumn_(app_column)
        
        display_column = NSTableColumn.alloc().initWithIdentifier_("display")
        display_column.setTitle_("Display")
        display_column.setWidth_(150)
        self.rules_table.addTableColumn_(display_column)
        
        behavior_column = NSTableColumn.alloc().initWithIdentifier_("behavior")
        behavior_column.setTitle_("Behavior")
        behavior_column.setWidth_(150)
        self.rules_table.addTableColumn_(behavior_column)
        
        maximize_column = NSTableColumn.alloc().initWithIdentifier_("maximize")
        maximize_column.setTitle_("Maximize")
        maximize_column.setWidth_(100)
        self.rules_table.addTableColumn_(maximize_column)
        
        self.rules_table.setHeaderView_(None)
        self.rules_table.setDataSource_(self)
        self.rules_table.setDelegate_(self)
        
        scroll_view.setDocumentView_(self.rules_table)
        scroll_view.setHasVerticalScroller_(True)
        content_view.addSubview_(scroll_view)
        
        # display_rules is already initialized in init()
        
        return box
    
    def create_display_rule_box(self, title, display_key, frame):
        """Create a display rule configuration box"""
        box = NSBox.alloc().initWithFrame_(frame)
        box.setTitle_(title)
        
        content_view = box.contentView()
        
        # App dropdown
        app_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(10, 60, 200, 25))
        app_popup.addItemsWithTitles_(self.available_apps)
        content_view.addSubview_(app_popup)
        
        # Behavior dropdown
        behavior_popup = NSPopUpButton.alloc().initWithFrame_(NSMakeRect(10, 30, 200, 25))
        behavior_popup.addItemsWithTitles_(["keep_same", "maximize", "minimize"])
        content_view.addSubview_(behavior_popup)
        
        # Maximize checkbox
        maximize_checkbox = NSButton.alloc().initWithFrame_(NSMakeRect(10, 5, 150, 20))
        maximize_checkbox.setTitle_("Maximize")
        maximize_checkbox.setButtonType_(3)  # NSSwitchButton
        content_view.addSubview_(maximize_checkbox)
        
        # Add button
        add_button = NSButton.alloc().initWithFrame_(NSMakeRect(170, 30, 60, 25))
        add_button.setTitle_("Add")
        add_button.setButtonType_(1)
        add_button.setTarget_(self)
        add_button.setAction_('addDisplayRule:')
        content_view.addSubview_(add_button)
        
        elements = {
            "app_popup": app_popup,
            "behavior_popup": behavior_popup,
            "maximize_checkbox": maximize_checkbox,
            "add_button": add_button
        }
        
        return box, elements
    
    def addStartupApp_(self, sender):
        """Add app to startup keep open list"""
        selected_index = self.startup_app_popup.indexOfSelectedItem()
        if selected_index >= 0:
            app = self.available_apps[selected_index]
            if app not in self.startup_apps:
                self.startup_apps.append(app)
                self.startup_table.reloadData()
    
    def addDisplayRule_(self, sender):
        """Add a display rule"""
        # Find which display_key this button belongs to
        display_key = None
        for key, elements in self.display_ui_elements.items():
            if elements.get("add_button") == sender:
                display_key = key
                break
        
        if not display_key:
            return
        
        # Get UI elements for this display
        elements = self.display_ui_elements.get(display_key)
        if not elements:
            return
        
        # Get app from popup
        app_popup = elements["app_popup"]
        app_index = app_popup.indexOfSelectedItem()
        if app_index < 0:
            return
        
        app = self.available_apps[app_index]
        
        # Get behavior
        behavior_popup = elements["behavior_popup"]
        behavior_index = behavior_popup.indexOfSelectedItem()
        behaviors = ["keep_same", "maximize", "minimize"]
        behavior = behaviors[behavior_index] if behavior_index >= 0 else "keep_same"
        
        # Get maximize
        maximize_checkbox = elements["maximize_checkbox"]
        maximize = maximize_checkbox.state() == 1
        
        # Add rule
        rule = {
            "app": app,
            "behavior": behavior,
            "maximize": maximize
        }
        
        if display_key not in self.display_rules:
            self.display_rules[display_key] = []
        
        # Remove existing rule for this app
        self.display_rules[display_key] = [
            r for r in self.display_rules[display_key] 
            if r.get("app") != app
        ]
        
        self.display_rules[display_key].append(rule)
        self.rules_table.reloadData()
    
    def load_configuration(self):
        """Load current configuration"""
        # Load startup apps
        startup_rules = self.registry.get_startup_rules()
        self.startup_apps = startup_rules.get("keep_open", [])
        self.startup_table.reloadData()
        
        # Load display rules
        self.display_rules = {
            "w1": self.registry.get_display_rules("w1"),
            "w2": self.registry.get_display_rules("w2"),
            "laptop": self.registry.get_display_rules("laptop")
        }
        self.rules_table.reloadData()
    
    def saveConfiguration_(self, sender):
        """Save configuration"""
        # Save startup apps
        for app in self.startup_apps:
            self.registry.add_startup_app(app)
        
        # Remove apps not in list
        current_startup = self.registry.get_startup_rules().get("keep_open", [])
        for app in current_startup:
            if app not in self.startup_apps:
                self.registry.remove_startup_app(app)
        
        # Save display rules
        for display_key, rules in self.display_rules.items():
            for rule in rules:
                self.registry.add_display_rule(
                    display_key,
                    rule["app"],
                    rule.get("behavior", "keep_same"),
                    rule.get("maximize", False)
                )
        
        # Show success message
        alert = NSAlert.alloc().init()
        alert.setMessageText_("Configuration saved successfully!")
        alert.setAlertStyle_(NSInformationalAlertStyle)
        alert.runModal()
    
    # NSTableViewDataSource methods
    def numberOfRowsInTableView_(self, tableView):
        if tableView == self.startup_table:
            return len(getattr(self, 'startup_apps', []))
        elif tableView == self.rules_table:
            display_rules = getattr(self, 'display_rules', {})
            total = 0
            for rules in display_rules.values():
                total += len(rules)
            return total
        return 0
    
    def tableView_objectValueForTableColumn_row_(self, tableView, column, row):
        if tableView == self.startup_table:
            startup_apps = getattr(self, 'startup_apps', [])
            if row < len(startup_apps):
                return startup_apps[row]
        elif tableView == self.rules_table:
            # Flatten rules
            all_rules = []
            display_rules = getattr(self, 'display_rules', {})
            for display_key in ["w1", "w2", "laptop"]:
                for rule in display_rules.get(display_key, []):
                    all_rules.append({
                        "app": rule["app"],
                        "display": display_key,
                        "behavior": rule.get("behavior", "keep_same"),
                        "maximize": rule.get("maximize", False)
                    })
            
            if row < len(all_rules):
                rule = all_rules[row]
                col_id = column.identifier()
                if col_id == "app":
                    return rule["app"]
                elif col_id == "display":
                    return rule["display"]
                elif col_id == "behavior":
                    return rule["behavior"]
                elif col_id == "maximize":
                    return "Yes" if rule["maximize"] else "No"
        return None


def main():
    """Main entry point"""
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(0)  # NSApplicationActivationPolicyRegular
    
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    
    gui = SolonGUI.alloc().init()
    gui.showWindow_(None)
    gui.window().makeKeyAndOrderFront_(None)
    
    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == '__main__':
    main()

