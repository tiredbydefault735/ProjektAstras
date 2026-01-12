"""FoodSource entity."""


class FoodSource:
    """Nahrungsplatz auf der Map."""

    def __init__(self, x, y, amount):
        self.x = x
        self.y = y
        self.amount = amount
        self.max_amount = amount
        self.regeneration_timer = 0

    def consume(self, requested_amount):
        """Konsumiere Nahrung, gibt tatsächlich konsumierte Menge zurück."""
        consumed = min(requested_amount, self.amount)
        self.amount -= consumed
        return consumed

    def regenerate(self):
        """Regeneriere Nahrung über Zeit (alle 50 Steps = 5 Sekunden)."""
        self.regeneration_timer += 1
        if self.regeneration_timer >= 50:
            self.regeneration_timer = 0
            if self.amount < self.max_amount:
                self.amount = min(self.amount + 5, self.max_amount)

    def is_depleted(self):
        """Ist die Nahrung aufgebraucht?"""
        return self.amount <= 0
