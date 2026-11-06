#!/usr/bin/env python3
"""Hyprland Settings - GUI for Hyprland options, binds, rules and more."""
import gi, json, os, subprocess, sys
gi.require_version("Gtk", "4.0"); gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

HYPR = os.path.expanduser("~/.config/hypr")
CONF = f"{HYPR}/hyprland-settings.conf"   # managed file (sourced by hyprland.conf)
MAIN = f"{HYPR}/hyprland.conf"

# page -> [(key, label, type, arg)]   types: bool, int, float, choice, str
PAGES = {
 "General": [
  ("general:gaps_in", "Inner gaps", "int", (0, 100, 1)),
  ("general:gaps_out", "Outer gaps", "int", (0, 200, 1)),
  ("general:border_size", "Border size", "int", (0, 20, 1)),
  ("general:col.active_border", "Active border color (e.g. rgba(33ccffee))", "str", None),
  ("general:col.inactive_border", "Inactive border color", "str", None),
  ("general:layout", "Layout", "choice", ["dwindle", "master"]),
  ("general:resize_on_border", "Resize on border", "bool", None),
  ("general:allow_tearing", "Allow tearing", "bool", None)],
 "Decoration": [
  ("decoration:rounding", "Corner rounding", "int", (0, 50, 1)),
  ("decoration:active_opacity", "Active opacity", "float", (0.1, 1, 0.05)),
  ("decoration:inactive_opacity", "Inactive opacity", "float", (0.1, 1, 0.05)),
  ("decoration:blur:enabled", "Blur", "bool", None),
  ("decoration:blur:size", "Blur size", "int", (1, 30, 1)),
  ("decoration:blur:passes", "Blur passes", "int", (1, 10, 1)),
  ("decoration:shadow:enabled", "Shadows", "bool", None),
  ("decoration:shadow:range", "Shadow range", "int", (0, 100, 1))],
 "Animations": [
  ("animations:enabled", "Enable animations", "bool", None)],
 "Input": [
  ("input:kb_layout", "Keyboard layout", "str", None),
  ("input:kb_variant", "Keyboard variant", "str", None),
  ("input:kb_options", "Keyboard options", "str", None),
  ("input:follow_mouse", "Follow mouse", "choice", ["0", "1", "2", "3"]),
  ("input:sensitivity", "Mouse sensitivity", "float", (-1, 1, 0.05)),
  ("input:repeat_rate", "Key repeat rate", "int", (1, 100, 1)),
  ("input:repeat_delay", "Key repeat delay (ms)", "int", (100, 2000, 50)),
  ("input:touchpad:natural_scroll", "Touchpad natural scroll", "bool", None),
  ("input:touchpad:tap-to-click", "Tap to click", "bool", None),
  ("input:touchpad:disable_while_typing", "Disable while typing", "bool", None)],
 "Gestures": [
  ("gestures:workspace_swipe", "Workspace swipe", "bool", None)],
 "Misc": [
  ("misc:disable_hyprland_logo", "Disable logo", "bool", None),
  ("misc:disable_splash_rendering", "Disable splash", "bool", None),
  ("misc:vfr", "Variable frame rate", "bool", None),
  ("misc:vrr", "Variable refresh rate", "choice", ["0", "1", "2"]),
  ("misc:mouse_move_enables_dpms", "Mouse wakes display", "bool", None),
  ("misc:key_press_enables_dpms", "Key press wakes display", "bool", None),
  ("misc:focus_on_activate", "Focus on activate", "bool", None)],
 "Dwindle": [
  ("dwindle:pseudotile", "Pseudotile", "bool", None),
  ("dwindle:preserve_split", "Preserve split", "bool", None),
  ("dwindle:force_split", "Force split", "choice", ["0", "1", "2"])],
}
# multi-line sections: key -> (title, hint)
LISTS = {
 "monitor": ("Monitors", "name,resolution@hz,position,scale   e.g. DP-1,2560x1440@144,0x0,1"),
 "exec-once": ("Autostart", "Commands run once at login, e.g. waybar"),
 "exec": ("Run on every reload", "Commands run on each config reload"),
 "env": ("Environment", "NAME,value   e.g. XCURSOR_SIZE,24"),
 "bind": ("Keybinds", "mods,key,dispatcher,arg   e.g. SUPER,Q,exec,kitty"),
 "bindm": ("Mouse binds", "e.g. SUPER,mouse:272,movewindow"),
 "bindel": ("Repeat/locked binds", "e.g. ,XF86AudioRaiseVolume,exec,wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+"),
 "windowrule": ("Window rules", "Use the syntax of your Hyprland version"),
 "layerrule": ("Layer rules", "e.g. blur,waybar"),
 "workspace": ("Workspaces", "e.g. 1,monitor:DP-1,default:true"),
 "bezier": ("Bezier curves", "name,x0,y0,x1,y1"),
 "animation": ("Animation rules", "name,on/off,speed,curve[,style]"),
}

values, lists = {}, {k: [] for k in LISTS}
if os.path.exists(CONF):
    for ln in open(CONF):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = (x.strip() for x in ln.split("=", 1))
            (lists[k].append(v) if k in lists else values.__setitem__(k, v))

def save():
    os.makedirs(HYPR, exist_ok=True)
    out = ["# Managed by hyprland-settings - manual edits may be overwritten"]
    out += [f"{k} = {v}" for k, v in values.items()]
    for k, items in lists.items():
        out += [f"{k} = {x}" for x in items]
    open(CONF, "w").write("\n".join(out) + "\n")

def hypr(*a):
    try: subprocess.Popen(["hyprctl", *a], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError: pass

def current(key):
    try:
        o = json.loads(subprocess.check_output(["hyprctl", "getoption", key, "-j"],
                       text=True, stderr=subprocess.DEVNULL))
        for t in ("int", "float", "str"):
            if t in o: return str(o[t])
    except Exception: pass
    return None

def setv(key, val):
    values[key] = val; hypr("keyword", key, val); save()

def make_row(key, label, typ, arg):
    v = values.get(key) or (current(key) if typ != "str" else "") or ""
    if typ == "bool":
        r = Adw.SwitchRow(title=label); r.set_active(v.lower() in ("1", "true", "yes", "on"))
        r.connect("notify::active", lambda w, _: setv(key, "true" if w.get_active() else "false"))
    elif typ in ("int", "float"):
        lo, hi, st = arg; fl = typ == "float"
        adj = Gtk.Adjustment(value=float(v or 0), lower=lo, upper=hi, step_increment=st, page_increment=st * 5)
        r = Adw.SpinRow(title=label, adjustment=adj, digits=2 if fl else 0)
        r.connect("notify::value", lambda w, _: setv(key, str(round(w.get_value(), 2)) if fl else str(int(w.get_value()))))
    elif typ == "choice":
        r = Adw.ComboRow(title=label, model=Gtk.StringList.new(arg))
        if v in arg: r.set_selected(arg.index(v))
        r.connect("notify::selected", lambda w, _: setv(key, arg[w.get_selected()]))
    else:
        r = Adw.EntryRow(title=label, show_apply_button=True); r.set_text(v if v != "[[EMPTY]]" else "")
        r.connect("apply", lambda w: setv(key, w.get_text()))
    r.set_tooltip_text(key)
    return r

def opt_page(items):
    p = Adw.PreferencesPage(); g = Adw.PreferencesGroup(); p.add(g)
    for it in items: g.add(make_row(*it))
    return p

def list_page(key, title, hint):
    p = Adw.PreferencesPage(); g = Adw.PreferencesGroup(title=title, description=hint); p.add(g)
    rows = []
    def sync(*_): lists[key] = [r.get_text().strip() for r in rows if r.get_text().strip()]; save()
    def add(text=""):
        r = Adw.EntryRow(title=key); r.set_text(text)
        b = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER); b.add_css_class("flat")
        def rm(_): g.remove(r); rows.remove(r); sync()
        b.connect("clicked", rm); r.add_suffix(b); r.connect("changed", sync)
        rows.append(r); g.add(r)
    for t in lists[key]: add(t)
    g2 = Adw.PreferencesGroup(); btn = Gtk.Button(label="Add entry"); btn.connect("clicked", lambda _: add())
    g2.add(btn); p.add(g2)
    return p

def raw_page():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
    tv = Gtk.TextView(monospace=True); sw = Gtk.ScrolledWindow(vexpand=True, child=tv)
    if os.path.exists(MAIN): tv.get_buffer().set_text(open(MAIN).read())
    def write(_):
        b = tv.get_buffer(); open(MAIN, "w").write(b.get_text(b.get_start_iter(), b.get_end_iter(), False)); hypr("reload")
    btn = Gtk.Button(label="Save hyprland.conf & reload", halign=Gtk.Align.END); btn.connect("clicked", write)
    box.append(sw); box.append(btn)
    return box

def activate(app):
    win = Adw.ApplicationWindow(application=app, title="Hyprland Settings", default_width=1000, default_height=700)
    stack = Gtk.Stack(hexpand=True)
    for n, items in PAGES.items(): stack.add_titled(opt_page(items), n, n)
    for k, (t, h) in LISTS.items(): stack.add_titled(list_page(k, t, h), k, t)
    stack.add_titled(raw_page(), "raw", "Raw hyprland.conf")
    side = Gtk.StackSidebar(stack=stack); side.set_size_request(220, -1)
    body = Gtk.Box(); body.append(side); body.append(stack)
    hb = Adw.HeaderBar(); b = Gtk.Button(label="Save & Reload"); b.add_css_class("suggested-action")
    b.connect("clicked", lambda _: (save(), hypr("reload"))); hb.pack_end(b)
    tv = Adw.ToolbarView(content=body); tv.add_top_bar(hb); win.set_content(tv); win.present()

app = Adw.Application(application_id="io.github.hyprland_settings")
app.connect("activate", activate)
sys.exit(app.run(sys.argv))
