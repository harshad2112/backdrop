"""The slideshow itself: images from the custom link, remote keys, transitions, credits."""
from conftest import FAKE_ZIP


def test_custom_link_images_are_shown(app):
    app.open({"image_url": FAKE_ZIP + "?n=3"})
    app.wait_for("() => images.length === 3")
    assert sorted(app.shown("zip")) == ["zip/01.jpg", "zip/02.jpg", "zip/03.jpg"]
    app.wait_for("() => document.querySelector('.layer.shown') !== null")
    src = app.js("() => document.querySelector('.layer.shown').src")
    assert "/files/downloads/backdrop-" in src


def test_no_custom_link_starts_with_random_photos(app):
    app.open({"image_url": ""}, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    assert app.setting("src_zip") == "0" and app.setting("src_picsum") == "1"


def test_quick_right_presses_never_leave_a_black_screen(app):
    # regression: a late transition clean-up used to hide the layer that had just become visible
    app.open({"image_url": FAKE_ZIP + "?n=3"})
    app.wait_for("() => images.length === 3 && document.querySelector('.layer.shown')")
    for _ in range(6):
        app.page.keyboard.press("ArrowRight")
        app.page.wait_for_timeout(150)
    app.page.wait_for_timeout(1500)  # let every transition and clean-up finish
    assert app.js("() => layers()[frontLayer].classList.contains('shown')")
    assert app.js("() => getComputedStyle(layers()[frontLayer]).opacity") == "1"


def test_left_right_do_nothing_with_one_image(app):
    app.open({"image_url": FAKE_ZIP + "?n=1"})
    app.wait_for("() => images.length === 1 && document.querySelector('.layer.shown')")
    before = app.js("() => layers()[frontLayer].src")
    app.press("right", "right", "left")
    app.page.wait_for_timeout(1300)
    assert app.js("() => layers()[frontLayer].src") == before
    assert app.js("() => layers()[frontLayer].classList.contains('shown')")


def test_short_credits(app):
    app.open({"image_url": ""}, {"keep": "10", "src_picsum": "0", "src_unsplash": "1",
                                 "unsplashThemes": ["nature"]})
    app.wait_for("() => images.length === 10")
    credits = app.js("() => images.map(creditText)")
    assert all(c.endswith(" · Unsplash") and c.startswith("Photographer ") for c in credits)
    assert app.js("() => creditText({ origin: 'picsum' })") == "Picsum"
    assert app.js("() => creditText({ origin: 'wallhaven' })") == "Wallhaven"
    assert app.js("() => creditText({ origin: 'zip' })") == ""
