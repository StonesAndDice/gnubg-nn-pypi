import unittest
import gnubg  # <--- Import the top-level package


class TestGnuBGFullEngine(unittest.TestCase):
    def test_engine_init(self):
        """Test that the full C engine can be initialized."""
        # This function comes from the new bridge (gnubg_bridge.cpp)
        self.assertTrue(hasattr(gnubg, "init_engine"), "init_engine not found in top-level package")

        # Try calling it. It should return None (void in C++)
        # Note: If this crashes, the GLib/Headless setup is incorrect.
        try:
            gnubg.init_engine()
        except Exception as e:
            self.fail(f"init_engine() raised an exception: {e}")

    def test_module_structure(self):
        """Ensure the namespace is clean."""
        # gnubg.nn should be accessible
        self.assertTrue(hasattr(gnubg, "nn"), "gnubg.nn submodule is missing")

        # Ensure we didn't accidentally pollute the top namespace
        # with neural net functions (unless intended).
        # For example, 'best_move' should be in gnubg.nn, not gnubg.
        self.assertFalse(hasattr(gnubg, "best_move"),
                         "best_move found in top level! It should be in gnubg.nn")
        self.assertTrue(hasattr(gnubg.nn, "best_move"),
                        "best_move missing from gnubg.nn")


if __name__ == '__main__':
    unittest.main()