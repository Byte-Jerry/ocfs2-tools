# OCFS2Console - GUI frontend for OCFS2 management and debugging
# Copyright (C) 2002, 2005 Oracle.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 021110-1307, USA.

import gtk

from guiutil import set_props, error_box, query_text

from partitionview import PartitionView
from menu import Menu
from toolbar import Toolbar
from about import about, process_gui_args
from process import Process
from format import format_partition
from tune import tune_label, tune_nodes
from general import General
from nodemap import NodeMap
from browser import Browser
from clconfig import cluster_configurator
from fsck import fsck_volume

info_items = (
    ('General',          General),
    ('File Listing',     Browser),
    ('Configured Nodes', NodeMap),
)

class Console(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        set_props(self, title='OCFS2 Console',
                        default_width=520,
                        default_height=420,
                        border_width=0)
        self.connect('delete_event', self.cleanup)

        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)

        info_frames = []

        for desc, info in info_items:
            frame = gtk.Frame()
            set_props(frame, shadow=gtk.SHADOW_NONE,
                             border_width=0)

            notebook.add_with_properties(frame, 'tab_label', desc)

            info_frames.append((frame, info))

        self.pv = PartitionView(info_frames)

        vbox = gtk.VBox()
        self.add(vbox)

        menu = Menu(self)

        menubar, unmounted_items = menu.get_widgets()
        vbox.pack_start(menubar, expand=False, fill=False)

        self.pv.add_unmount_widgets(unmounted_items)

        toolbar = Toolbar(self)

        tb, buttons, filter_entry = toolbar.get_widgets()
        vbox.pack_start(tb, expand=False, fill=False)

        self.pv.add_mount_widgets(buttons['unmount'])
        self.pv.add_unmount_widgets(buttons['mount'])

        filter_entry.connect('activate', self.refresh)

        self.pv.set_filter_entry(filter_entry)

        vpaned = gtk.VPaned()
        vpaned.set_border_width(4)
        vbox.pack_start(vpaned, expand=True, fill=True)

        scrl_win = gtk.ScrolledWindow()
        set_props(scrl_win, hscrollbar_policy=gtk.POLICY_AUTOMATIC,
                            vscrollbar_policy=gtk.POLICY_AUTOMATIC)
        scrl_win.add(self.pv)
        vpaned.pack1(scrl_win)

        vpaned.pack2(notebook)

        self.pv.grab_focus()
        self.show_all()

        self.refresh()

    def cleanup(self, *args):
        gtk.main_quit()

    def about(self):
        about(self)

    def refresh(self, *args):
        self.pv.refresh_partitions()

    def mount(self):
        device, mountpoint = self.pv.get_sel_values()

        mountpoint = query_text(self, 'Mountpoint')
        if not mountpoint:
            return

        command = ('mount', '-t', 'ocfs2', device, mountpoint)

        p = Process(command, 'Mount', 'Mounting...', self, spin_now=False)
        success, output, killed = p.reap()

        if not success:
            if killed:
                error_box(self, 'mount died unexpectedly! Your system is '
                                'probably in an inconsistent state. You '
                                'should reboot at the earliest opportunity')
            else:
                error_box(self, '%s: Could not mount %s' % (output, device))

    def unmount(self):
        device, mountpoint = self.pv.get_sel_values()

        command = ('umount', mountpoint)

        p = Process(command, 'Unmount', 'Unmounting...', self, spin_now=False)
        success, output, killed = p.reap()

        if not success:
            if killed:
                error_box(self, 'umount died unexpectedly! Your system is '
                                'probably in an inconsistent state. You '
                                'should reboot at the earliest opportunity')
            else:
                error_box(self, '%s: Could not unmount %s mounted on %s' %
                                (output, device, mountpoint))

    def format(self):
        format_partition(self, self.pv.get_device())

    def relabel(self):
        tune_label(self, self.pv.get_device())

    def node_num(self):
        tune_nodes(self, self.pv.get_device())

    def check(self):
        fsck_volume(self, self.pv.get_device(), check=True)

    def repair(self):
        fsck_volume(self, self.pv.get_device(), check=False)

    def clconfig(self):
        cluster_configurator(self)

def main():
    process_gui_args()
    console = Console()
    gtk.main()

if __name__ == '__main__':
    main()
