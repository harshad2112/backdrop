"""The settings overlay: menu, pages, layout and the Display / Clock options."""
import re

from conftest import FAKE_ZIP


def _start(app):
    app.open({"image_url": FAKE_ZIP + "?n=2"})
    app.wait_for("() => images.length === 2")


def test_menu_sections_and_back(app):
    _start(app)
    app.press("playpause")
    assert app.js("() => document.getElementById('overlay').classList.contains('open')")
    labels = app.js("() => [...document.querySelectorAll('.menu-item .label')].map(e => e.textContent)")
    assert labels == ["Display", "Clock", "Images", "Favorites", "Close"]

    app.press("ok")  # Display
    assert app.js("() => document.querySelector('#panel h1').textContent") == "‹  Display"
    app.press("back")  # back to the menu, on the section we came from
    assert app.js("() => document.querySelector('#panel h1').textContent") == "Backdrop settings"
    assert app.focused()["value"] == "slideshow"
    app.press("back")  # closes
    assert not app.js("() => document.getElementById('overlay').classList.contains('open')")


def test_play_pause_closes_from_any_page(app):
    _start(app)
    app.open_settings_page(1)
    app.press("playpause")
    assert not app.js("() => settingsOpen")


def test_panel_is_the_same_size_on_every_page(app):
    _start(app)
    app.press("playpause")
    app.page.wait_for_timeout(400)
    box = lambda: app.js("() => { var r = document.getElementById('panel').getBoundingClientRect();"
                         " return [Math.round(r.width), Math.round(r.height)]; }")
    sizes = [box()]
    for i in range(4):
        app.press(*["down"] * i)
        app.press("ok")
        app.page.wait_for_timeout(400)
        sizes.append(box())
        app.press("back")
        app.page.wait_for_timeout(300)
        app.press(*["up"] * 5)
    assert len(set(map(tuple, sizes))) == 1, sizes


def test_focused_item_is_not_clipped(app):
    # regression: the scroll area clipped the left edge of the enlarged, glowing focused item
    _start(app)
    app.press("playpause")
    app.page.wait_for_timeout(400)
    # in TV pixels (the dev page is scaled to fit the browser window)
    gap = app.js("() => { var f = document.querySelector('#panel .focused').getBoundingClientRect();"
                 " var b = document.getElementById('panelBody').getBoundingClientRect();"
                 " return (f.left - b.left) / (parseFloat(document.documentElement.style.zoom) || 1); }")
    assert gap >= 4, gap  # room for the 3px glow around the focused item


def test_messages_show_above_the_settings(app):
    # regression: "Mark favorites with OK first" appeared behind the menu
    _start(app)
    toast = int(app.js("() => getComputedStyle(document.getElementById('toast')).zIndex"))
    overlay = int(app.js("() => getComputedStyle(document.getElementById('overlay')).zIndex"))
    assert toast > overlay


def test_images_tabs_switch_and_up_lands_on_the_open_tab(app):
    _start(app)
    app.open_settings_page(2)  # Images, tab bar focused on General
    assert app.focused() == {"action": "tab", "value": "general", "text": "General"}
    app.press("right", "right")  # Custom link, Picsum
    assert app.js("() => imagesTab") == "picsum"
    app.press("down")  # into the Picsum tab
    assert app.focused()["action"] == "switch"
    # regression: moving up used to land on General
    app.press("up")
    assert app.focused()["value"] == "picsum"


LAST_NOTE_VISIBLE = """() => {
    var body = document.getElementById('panelBody');
    var notes = body.querySelectorAll('.hint');
    var note = notes[notes.length - 1].getBoundingClientRect();
    var focused = document.querySelector('#panel .focused').getBoundingClientRect();
    var b = body.getBoundingClientRect();
    return note.bottom <= b.bottom + 1 && focused.top >= b.top - 1;
}"""


def test_last_row_scrolls_far_enough_to_read_the_note_below_it(app):
    # regression: the note under the last button (e.g. under "Update all now") could never be scrolled to
    app.open({"image_url": FAKE_ZIP + "?n=8"})
    app.wait_for("() => images.length === 8")
    for i in range(8):  # 8 favorites -> two rows of thumbnails, so the Favorites page needs scrolling
        app.js("n => favorite(images.find(i => i.name === n))", f"zip/{i + 1:02d}.jpg")
        app.wait_for("n => getManifest('favorites').length === n", i + 1)
    app.open_settings_page(3)
    assert app.js("() => { var b = document.getElementById('panelBody'); return b.scrollHeight > b.clientHeight; }")
    app.press("down", "down", "down", "down")  # switches, two grid rows, then the Delete button row
    assert app.focused()["action"] == "favdelete"
    app.page.wait_for_timeout(800)  # smooth scroll
    assert app.js(LAST_NOTE_VISIBLE)

    app.press("back")
    app.press("up", "ok")  # Images
    app.press("down", "down", "down")  # General: kept, get new, Update all now
    assert app.focused()["action"] == "refresh"
    app.page.wait_for_timeout(800)
    assert app.js(LAST_NOTE_VISIBLE)


def test_brightness_slider(app):
    _start(app)
    app.open_settings_page(0)
    app.press("down", "down")  # time per image, transition, brightness
    assert app.focused()["action"] == "brightness"
    app.press("left", "left")
    assert app.setting("brightness") == "90"
    assert app.js("() => document.getElementById('dim').style.opacity") == "0.1"
    app.press(*["left"] * 30)
    assert app.setting("brightness") == "10"  # never fully black


def test_clock_options(app):
    _start(app)
    app.open_settings_page(1)
    app.press("ok")  # Show clock
    assert app.js("() => document.getElementById('clock').classList.contains('on')")
    app.press("down", "ok")  # 24-hour clock
    time_text = app.js("() => document.querySelector('#clock .time').textContent")
    assert re.fullmatch(r"\d\d:\d\d", time_text), time_text
    assert app.js("() => document.querySelector('#clock .ampm').textContent") == ""
    app.press("down", "ok")  # Show date
    assert app.js("() => document.querySelector('#clock .date').textContent") != ""
    app.press("down", "ok")  # Show seconds
    app.page.wait_for_timeout(1100)
    assert re.fullmatch(r"\d\d:\d\d:\d\d", app.js("() => document.querySelector('#clock .time').textContent"))


def test_display_order_and_credits_switches(app):
    _start(app)
    app.open_settings_page(0)
    app.press("down", "down", "down", "right", "ok")  # Order: Shuffle
    assert app.setting("order") == "shuffle"
    app.press("down", "ok")  # Show photo credits: off
    assert app.setting("showCredits") == "0"
