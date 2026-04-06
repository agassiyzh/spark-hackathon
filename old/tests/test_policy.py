import unittest

from orchestrator.policy import PolicyEngine


class PolicyEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = PolicyEngine(auto_execute_entities={"light.living_room"})

    def test_whitelisted_light_can_auto_execute(self) -> None:
        decision = self.policy.evaluate_control(
            domain="light",
            entity_id="light.living_room",
            confirmed=False,
        )

        self.assertTrue(decision.allow_execution)
        self.assertFalse(decision.requires_confirmation)

    def test_non_lighting_control_requires_confirmation(self) -> None:
        decision = self.policy.evaluate_control(
            domain="switch",
            entity_id="switch.heater",
            confirmed=False,
        )

        self.assertFalse(decision.allow_execution)
        self.assertTrue(decision.requires_confirmation)

    def test_confirmation_unlocks_non_lighting_control(self) -> None:
        decision = self.policy.evaluate_control(
            domain="switch",
            entity_id="switch.heater",
            confirmed=True,
        )

        self.assertTrue(decision.allow_execution)
        self.assertFalse(decision.requires_confirmation)


if __name__ == "__main__":
    unittest.main()
