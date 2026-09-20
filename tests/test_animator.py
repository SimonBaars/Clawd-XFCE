from clippy_xfce.animator import Animator, MOOD_ANIMATIONS
from clippy_xfce.sprites import load_agent_definition


def test_rest_and_queue():
    agent = load_agent_definition()
    player = Animator(agent)
    view = player.current_view()
    assert view.images
    assert view.duration_ms >= 50
    player.play("Wave", interrupt=True)
    assert player.current == "Wave"
    player.play("Writing")
    assert "Writing" in player.queue
    player.stop()
    assert player.exiting


def test_advance_reaches_rest():
    agent = load_agent_definition()
    player = Animator(agent)
    player.play("RestPose", interrupt=True)
    seen = set()
    for _ in range(8):
        view = player.advance()
        seen.add(view.animation)
    assert player.current in agent.animations


def test_moods_exist():
    agent = load_agent_definition()
    for names in MOOD_ANIMATIONS.values():
        assert any(name in agent.animations for name in names)
