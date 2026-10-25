"""Favorites: saving with OK, where the image lives, and deleting only from Settings → Favorites."""
from conftest import FAKE_ZIP


def _current(app):
    return app.js("() => playlist[slideIndex].name")


def test_ok_saves_an_online_image_and_moves_it_out_of_its_source(app):
    app.open({"image_url": ""}, {"keep": "10"})
    app.wait_for("() => images.length === 10 && document.querySelector('.layer.shown')")
    app.wait_idle()
    name = _current(app)
    file = name.split("/", 1)[1]
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 1")
    assert file in app.files("backdrop-favorites")
    assert file not in app.files("backdrop-picsum")  # moved, not copied
    assert all(m["file"] != file for m in app.manifest("picsum"))
    app.wait_for("() => playlist[slideIndex] && playlist[slideIndex].source === 'favorites'")
    # the corner updates once the image has loaded from its new place
    app.wait_for("() => document.getElementById('credit').textContent.indexOf('♥') === 0", timeout=5000)


def test_custom_link_favorite_shows_only_once(app):
    # regression: the ZIP image stayed in Custom link as well as in Favorites
    app.open({"image_url": FAKE_ZIP + "?n=3"})
    app.wait_for("() => images.length === 3 && document.querySelector('.layer.shown')")
    file = _current(app).split("/", 1)[1]
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 1")
    app.wait_for("() => images.some(i => i.source === 'favorites')")  # the list has been reloaded
    assert "zip/" + file not in app.shown("zip")
    assert len(app.shown("zip")) == 2 and len(app.shown("favorites")) == 1
    assert file in app.files(app.setting("activeDir"))  # the original stays (the ZIP folder gets replaced)


def test_ok_on_a_favorite_never_removes_it(app):
    app.open({"image_url": FAKE_ZIP + "?n=2"})
    app.wait_for("() => images.length === 2 && document.querySelector('.layer.shown')")
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 1")
    app.js("() => { localStorage.setItem('favOnly', '1'); reloadImages(function() { rebuildPlaylist(null); }); }")
    app.wait_for("() => playlist.length === 1 && playlist[0].source === 'favorites'")
    app.page.wait_for_timeout(1200)
    app.press("ok")
    app.page.wait_for_timeout(300)
    assert "Already a favorite" in app.js("() => document.getElementById('toast').textContent")
    assert len(app.manifest("favorites")) == 1


def test_favorites_only_falls_back_to_everything_when_empty(app):
    app.open({"image_url": FAKE_ZIP + "?n=2"}, {"favOnly": "1"})
    app.wait_for("() => images.length === 2")
    assert app.js("() => playlist.length") == 2


def test_deleting_a_favorite_needs_two_presses(app):
    app.open({"image_url": FAKE_ZIP + "?n=2"})
    app.wait_for("() => images.length === 2 && document.querySelector('.layer.shown')")
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 1")
    app.page.wait_for_timeout(300)

    app.open_settings_page(3)  # Favorites
    app.press("down", "down")  # show-in-slideshow, favorites only, grid
    assert app.focused()["action"] == "favmark"
    app.press("ok")  # mark
    app.press("down")  # Delete marked (1)
    assert app.focused()["text"] == "Delete marked (1)"
    app.press("ok")
    assert app.focused()["text"] == "Press OK again to delete 1"
    assert len(app.manifest("favorites")) == 1  # nothing deleted yet
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 0")
    assert app.files("backdrop-favorites") == []


def test_delete_with_nothing_marked_explains_itself(app):
    app.open({"image_url": FAKE_ZIP + "?n=2"})
    app.wait_for("() => images.length === 2 && document.querySelector('.layer.shown')")
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 1")
    app.open_settings_page(3)
    app.press("down", "down", "down")  # Delete marked (0)
    app.press("ok")
    assert "Mark favorites with OK first" in app.js("() => document.getElementById('toast').textContent")
    assert len(app.manifest("favorites")) == 1


def test_favorites_survive_refresh_and_reload(app):
    app.open({"image_url": ""}, {"keep": "10"})
    app.wait_for("() => images.length === 10 && document.querySelector('.layer.shown')")
    app.wait_idle()
    app.press("ok")
    app.wait_for("() => getManifest('favorites').length === 1")
    app.js("() => refreshAll('reload', null, ['picsum'])")
    app.wait_idle(800)
    app.js("() => refreshAll('update')")
    app.wait_idle(800)
    assert len(app.manifest("favorites")) == 1
    assert len(app.files("backdrop-favorites")) == 1
