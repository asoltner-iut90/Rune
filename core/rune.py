from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.binding import Binding
from core.pty_widget import PTYWidget
from core.sidebar import Sidebar
from core.workspace import Workspace

class Rune(App):
    BINDINGS = [
        Binding("ctrl+up", "navigate('up')", show=False),
        Binding("ctrl+down", "navigate('down')", show=False),
        Binding("ctrl+left", "navigate('left')", show=False),
        Binding("ctrl+right", "navigate('right')", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Horizontal(
    Sidebar(),
            Workspace(
                PTYWidget(command=["bash"]),
            )
        )

    def on_mount(self) -> None:
        # Donne le focus au premier élément par défaut
        if self.screen.focusable:
            self.screen.focusable[0].focus()

    def action_navigate(self, direction: str) -> None:
        focused = self.focused
        if not focused or not focused.can_focus:
            return

        # On récupère la région absolue du widget actuellement focus
        current_reg = focused.region

        # On cherche tous les widgets de l'écran qui sont VRAIMENT focusables
        focusable_widgets = [w for w in self.screen.query("*") if w.focusable]

        # On filtre pour exclure le widget déjà sélectionné
        candidates = [w for w in focusable_widgets if w is not focused]

        best_candidate = None

        if direction == "right":
            # w.region.x doit être plus à droite que le bord droit du widget actuel
            right_side = [w for w in candidates if w.region.x >= current_reg.right]
            if right_side:
                best_candidate = min(right_side, key=lambda w: w.region.x)

        elif direction == "left":
            # Le bord droit de w doit être plus à gauche que le bord gauche du widget actuel
            left_side = [w for w in candidates if w.region.right <= current_reg.x]
            if left_side:
                best_candidate = max(left_side, key=lambda w: w.region.right)

        elif direction == "up":
            # Le bas de w doit être plus haut que le haut du widget actuel
            above = [w for w in candidates if w.region.bottom <= current_reg.y]
            if above:
                best_candidate = max(above, key=lambda w: w.region.bottom)

        elif direction == "down":
            # Le haut de w doit être plus bas que le bas du widget actuel
            below = [w for w in candidates if w.region.y >= current_reg.bottom]
            if below:
                best_candidate = min(below, key=lambda w: w.region.y)

        if best_candidate:
            best_candidate.focus()