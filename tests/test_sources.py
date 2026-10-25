"""Online image sources: downloading, limits, themes/categories, reload and clean-up."""
from collections import Counter

ONLY = {"image_url": ""}  # no custom link


def _themes(app, source):
    return Counter(m.get("theme") for m in app.manifest(source))


def _shown_themes(app, source):
    return Counter(app.js("s => images.filter(i => i.source === s).map(i => "
                          "getManifest(s).find(m => s + '/' + m.file === i.name).theme)", source))


def _categories(app, source="wallhaven"):
    return Counter(app.js("s => images.filter(i => i.source === s).map(i => "
                          "getManifest(s).find(m => s + '/' + m.file === i.name).category)", source))


def test_picsum_fills_up_to_the_limit_without_duplicates(app):
    app.open(ONLY, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    keys = [m["key"] for m in app.manifest("picsum")]
    assert len(keys) == 10 and len(set(keys)) == 10
    assert len(app.files("backdrop-picsum")) == 10


def test_saved_images_are_reused_after_restart(app):
    app.open(ONLY, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    downloads = len(app.download_log())
    app.page.reload()
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    assert len(app.download_log()) == downloads  # nothing downloaded again


def test_unsplash_themes_share_the_limit_equally(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature", "ocean"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    assert _shown_themes(app, "unsplash") == {"nature": 5, "ocean": 5}


def test_unselected_theme_is_hidden_kept_and_comes_back_without_downloading(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature", "ocean"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()

    app.js("() => { localStorage.setItem('unsplashThemes', JSON.stringify(['nature'])); themesChanged(); }")
    app.wait_for("() => images.length === 10 && !refreshing")  # nature now gets all 10
    app.wait_idle(1500)
    assert _shown_themes(app, "unsplash") == {"nature": 10}
    assert _themes(app, "unsplash")["ocean"] == 5  # hidden, not deleted

    downloads = len(app.download_log())
    app.js("() => { localStorage.setItem('unsplashThemes', JSON.stringify(['nature', 'ocean'])); themesChanged(); }")
    app.wait_idle(1500)
    assert _shown_themes(app, "unsplash") == {"nature": 5, "ocean": 5}
    assert len(app.download_log()) == downloads  # ocean came back from storage


def test_wallhaven_adding_a_category_downloads_its_share(app):
    # regression: adding Anime to People showed nothing new, because the limit was only split by theme
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_wallhaven": "1", "whCategories": ["people"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    assert _categories(app) == {"people": 10}

    app.js("() => { localStorage.setItem('whCategories', JSON.stringify(['people', 'anime'])); themesChanged(); }")
    app.wait_for("() => images.filter(i => i.source === 'wallhaven').length === 10 && !refreshing")
    app.wait_idle(1500)
    assert _categories(app) == {"people": 5, "anime": 5}
    assert Counter(m["category"] for m in app.manifest("wallhaven"))["people"] == 10  # extras kept, hidden


def test_reload_replaces_a_sources_images(app):
    app.open(ONLY, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    old = {m["file"] for m in app.manifest("picsum")}

    app.js("() => refreshAll('reload', null, ['picsum'])")
    app.wait_idle(800)
    new = {m["file"] for m in app.manifest("picsum")}
    assert len(new) == 10 and not (old & new)
    assert set(app.files("backdrop-picsum")) == new  # old files deleted


def test_reload_also_clears_unselected_themes(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature", "ocean"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    app.js("() => { localStorage.setItem('unsplashThemes', JSON.stringify(['nature'])); }")
    app.js("() => refreshAll('reload', null, ['unsplash'])")
    app.wait_idle(800)
    assert _themes(app, "unsplash") == {"nature": 10}


def test_lower_limit_hides_extras_then_update_trims(app):
    app.open(ONLY, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    app.js("() => { localStorage.setItem('keep', '6'); reloadImages(); }")
    app.wait_for("() => images.length === 6")
    assert len(app.manifest("picsum")) == 10  # only hidden so far

    app.js("() => refreshAll('update')")
    app.wait_idle(800)
    assert len(app.manifest("picsum")) == 6
    assert len(app.files("backdrop-picsum")) == 6


def test_turning_a_source_off_hides_but_keeps_its_images(app):
    app.open(ONLY, {"keep": "10", "src_wallhaven": "1"})
    app.wait_for("() => images.length === 20")
    app.wait_idle()
    app.js("() => { localStorage.setItem('src_picsum', '0'); reloadImages(); }")
    app.wait_for("() => images.length === 10")
    assert app.shown("picsum") == []
    assert len(app.files("backdrop-picsum")) == 10


def test_unselected_marks_survive_for_hidden_images(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature", "ocean"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    ocean = app.js("() => images.find(i => getManifest('unsplash').find(m => 'unsplash/' + m.file === i.name"
                   " && m.theme === 'ocean')).name")
    app.js("n => setExcluded([n])", ocean)
    app.js("() => { localStorage.setItem('unsplashThemes', JSON.stringify(['nature'])); }")
    app.js("() => refreshAll('update')")
    app.wait_idle(800)
    assert app.js("() => getExcluded()") == [ocean]


def test_leftover_files_are_cleaned_up(app):
    app.open(ONLY, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    app.js("() => fetch('/fs?op=download&url=' + encodeURIComponent('https://picsum.photos/id/1/10/10.jpg')"
           " + '&dir=downloads/backdrop-picsum&name=stray.jpg')")
    app.page.wait_for_timeout(300)
    assert "stray.jpg" in app.files("backdrop-picsum")
    app.js("() => refreshAll('auto')")
    app.wait_idle(800)
    assert "stray.jpg" not in app.files("backdrop-picsum")


def _hidden(app, source):
    return app.js("s => hiddenEntries(s, getManifest(s)).map(m => m.theme)", source)


def _cycle_unsplash_themes(app, themes):
    """Select each theme on its own in turn, waiting for its images, so the others pile up as hidden."""
    for theme in themes:
        app.js("t => { localStorage.setItem('unsplashThemes', JSON.stringify([t])); themesChanged(); }", theme)
        # every Unsplash image on screen is of the new theme (an image that was just moved to
        # favorites can briefly still be listed, so a missing manifest entry means "not yet")
        app.wait_for("t => { var u = images.filter(i => i.source === 'unsplash'); return u.length === 10 && "
                     "u.every(i => { var m = getManifest('unsplash').find(m => 'unsplash/' + m.file === i.name);"
                     " return m && m.theme === t; }); }", theme)
        app.wait_idle(1500)


def test_hidden_images_are_capped_at_the_limit_on_update(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    _cycle_unsplash_themes(app, ["ocean", "space"])  # nature and ocean now hidden: 20 > limit 10
    assert Counter(_hidden(app, "unsplash")) == {"nature": 10, "ocean": 10}

    app.js("() => refreshAll('update')")
    app.wait_idle(800)
    assert Counter(_hidden(app, "unsplash")) == {"ocean": 10}  # the oldest hidden (nature) went first
    assert _shown_themes(app, "unsplash") == {"space": 10}  # what's on screen is untouched
    assert sorted(m["file"] for m in app.manifest("unsplash")) == app.files("backdrop-unsplash")


def test_selection_changes_alone_never_apply_the_cap(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature"]})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    _cycle_unsplash_themes(app, ["ocean", "space"])
    assert len(app.manifest("unsplash")) == 30, _themes(app, "unsplash")  # 20 hidden kept until a scheduled update


def test_clear_hidden_images_needs_two_presses_and_keeps_what_is_shown(app):
    app.open(ONLY, {"keep": "10", "src_picsum": "0", "src_unsplash": "1", "unsplashThemes": ["nature"]})
    app.wait_for("() => images.length === 10 && document.querySelector('.layer.shown')")
    app.wait_idle()
    app.press("ok")  # a favorite, which must survive
    app.wait_for("() => getManifest('favorites').length === 1")
    _cycle_unsplash_themes(app, ["ocean"])
    hidden = len(_hidden(app, "unsplash"))
    assert hidden == 9  # nature, minus the one moved to favorites
    shown = sorted(app.shown("unsplash"))

    app.open_settings_page(2)  # Images, General tab
    app.press("down", "down", "down", "right")
    assert app.focused()["text"] == f"Clear hidden images ({hidden})"
    app.press("ok")
    assert app.focused()["text"] == f"Press OK again to clear {hidden}"
    assert len(_hidden(app, "unsplash")) == hidden  # nothing cleared yet
    app.press("ok")
    app.wait_for("() => hiddenCount() === 0")
    assert sorted(app.shown("unsplash")) == shown
    assert len(app.manifest("favorites")) == 1
    assert sorted(m["file"] for m in app.manifest("unsplash")) == app.files("backdrop-unsplash")


def test_storage_is_shown_in_the_general_tab(app):
    app.open(ONLY, {"keep": "10"})
    app.wait_for("() => images.length === 10")
    app.wait_idle()
    app.open_settings_page(2)
    app.wait_for("() => /MB/.test(document.querySelector('[data-storage=\"total\"]').textContent)")
    lines = app.js("() => [...document.querySelectorAll('.source-status')].map(e => e.textContent)")
    assert any(line.startswith("●  Picsum  ·  10 images") and line.endswith("MB") for line in lines), lines
    assert any(line.startswith("♥  Favorites") for line in lines), lines
    assert any(line.startswith("Storage used on the TV") and line.endswith("MB") for line in lines), lines
