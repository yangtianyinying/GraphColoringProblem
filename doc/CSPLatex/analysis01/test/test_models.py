import unittest

from agent.models import (
    CANONICAL_FAMILIES,
    FAMILY_ORDER,
    all_family_posteriors,
    edge_strengths_cluster,
    edge_strengths_star,
    family_posterior,
)


class TestSixFamilies(unittest.TestCase):
    def setUp(self) -> None:
        # 0 is target; graph chosen to contain shell-2 nodes.
        self.adjacency = (
            (1, 2),
            (0, 3, 4),
            (0, 3),
            (1, 2),
            (1,),
        )
        self.target = 0
        # Soft evidence only on non-target nodes.
        self.evidence = {
            1: (0.9, 0.05, 0.05),
            2: (0.7, 0.15, 0.15),
            3: (0.5, 0.25, 0.25),
            4: (0.3, 0.35, 0.35),
        }

    def test_all_families_return_distribution(self) -> None:
        rows = all_family_posteriors(self.adjacency, self.target, self.evidence)
        self.assertEqual([row.family for row in rows], list(FAMILY_ORDER))
        for row in rows:
            posterior = row.posterior
            self.assertEqual(len(posterior), 3)
            self.assertAlmostEqual(sum(posterior), 1.0, places=10)
            for value in posterior:
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_endpoint_equivalence(self) -> None:
        m0 = family_posterior(self.adjacency, self.target, self.evidence, CANONICAL_FAMILIES["M_0"])
        rho0 = family_posterior(
            self.adjacency,
            self.target,
            self.evidence,
            {"family": "M_rho", "rho": 0.0, "beta": CANONICAL_FAMILIES["M_0"]["beta"]},
        )
        self.assertAlmostEqual(max(abs(a - b) for a, b in zip(m0, rho0)), 0.0, places=12)

        exact = family_posterior(self.adjacency, self.target, self.evidence, CANONICAL_FAMILIES["M_exact"])
        rho1 = family_posterior(
            self.adjacency,
            self.target,
            self.evidence,
            {"family": "M_rho", "rho": 1.0, "beta": CANONICAL_FAMILIES["M_exact"]["beta"]},
        )
        self.assertAlmostEqual(max(abs(a - b) for a, b in zip(exact, rho1)), 0.0, places=12)

    def test_star_strengths_match_distance_rule(self) -> None:
        strengths = edge_strengths_star(self.adjacency, self.target, beta=4.0)
        self.assertAlmostEqual(strengths[(0, 1)], 4.0)
        self.assertAlmostEqual(strengths[(0, 2)], 4.0)
        self.assertAlmostEqual(strengths[(0, 3)], 2.0)
        self.assertAlmostEqual(strengths[(0, 4)], 2.0)

    def test_cluster_adds_fill_in_edges(self) -> None:
        strengths = edge_strengths_cluster(self.adjacency, self.target, beta=4.0)
        # (1,2) are shell-1 nodes sharing shell-2 node 3, so fill-in should be present.
        self.assertIn((1, 2), strengths)
        self.assertAlmostEqual(strengths[(1, 2)], 4.0)

    def test_rho_beta_and_rho_same_when_parameters_same(self) -> None:
        rho = 0.35
        beta = 2.5
        model_a = family_posterior(
            self.adjacency,
            self.target,
            self.evidence,
            {"family": "M_rho", "rho": rho, "beta": beta},
        )
        model_b = family_posterior(
            self.adjacency,
            self.target,
            self.evidence,
            {"family": "M_rho,beta", "rho": rho, "beta": beta},
        )
        self.assertAlmostEqual(max(abs(a - b) for a, b in zip(model_a, model_b)), 0.0, places=12)


if __name__ == "__main__":
    unittest.main()
