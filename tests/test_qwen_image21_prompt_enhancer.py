import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


NODE_FILE = Path(__file__).resolve().parents[1] / "nodes" / "QwenImage21PromptEnhancerNode.py"
spec = importlib.util.spec_from_file_location("qwen_image21_prompt_enhancer", NODE_FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Node = module.QwenImage21PromptEnhancerNode


class QwenImage21PromptEnhancerTests(unittest.TestCase):
    def setUp(self):
        self.node = Node()
        self.inputs = dict(prompt='一根葱，画面中文字“葱 Pro”', system_prompt=module.DEFAULT_SYSTEM_PROMPT,
                           model="qwen3.8-27b", temperature=0.5, max_tokens=1024, timeout=30)

    def test_default_prompt_preserves_visual_and_typography_contract(self):
        prompt = module.DEFAULT_SYSTEM_PROMPT
        self.assertIn("one coherent paragraph", prompt)
        self.assertIn("character for character", prompt)
        self.assertIn("spatial order", prompt)
        self.assertIn("lighting a clear source", prompt)
        self.assertIn("do not put numeric aspect ratios", prompt)
        self.assertLessEqual(len(prompt), 12000)

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret", "ZMG_QWEN_PE_API_URL": "http://10.27.89.24/v1/chat/completions"})
    @patch("requests.post")
    def test_request_and_output(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content": 'A scallion floats against black. The text reads “葱 Pro”.'}}]})
        result = self.node.enhance(**self.inputs)
        self.assertEqual(result, ('A scallion floats against black. The text reads “葱 Pro”.',))
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-secret")
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "system")
        self.assertEqual(kwargs["json"]["messages"][1], {"role": "user", "content": self.inputs["prompt"]})
        self.assertFalse(kwargs["json"]["stream"])
        self.assertEqual(post.call_args.args[0], "http://10.27.89.24/v1/chat/completions")

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": ""})
    def test_missing_key_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "ZMG_GPUSTACK_API_KEY"):
            self.node.enhance(**self.inputs)

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret"})
    @patch("requests.post")
    def test_http_failure_does_not_leak_secret_or_body(self, post):
        post.return_value = Mock(status_code=500, text="test-secret internal error")
        with self.assertRaises(RuntimeError) as caught:
            self.node.enhance(**self.inputs)
        self.assertNotIn("test-secret", str(caught.exception))
        self.assertIn("500", str(caught.exception))

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret"})
    @patch("requests.post")
    def test_empty_response_fails_instead_of_bypassing_expansion(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content": ""}}]})
        with self.assertRaisesRegex(RuntimeError, "empty"):
            self.node.enhance(**self.inputs)

    def test_invalid_input_does_not_call_api(self):
        self.inputs["prompt"] = " "
        with self.assertRaises(ValueError):
            self.node.enhance(**self.inputs)

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": ""})
    @patch("requests.post")
    def test_node_api_key_works_without_server_environment(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content": "A finished image."}}]})
        result = self.node.enhance(**self.inputs, api_key="  widget-secret  ")
        self.assertEqual(result, ("A finished image.",))
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer widget-secret")

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "env-secret"})
    @patch("requests.post")
    def test_off_and_on_reasoning_modes_are_sent_to_api(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content": "A finished image."}}]})
        self.node.enhance(**self.inputs, reasoning_effort="off")
        self.assertEqual(post.call_args.kwargs["json"]["reasoning_effort"], "none")
        self.node.enhance(**self.inputs, reasoning_effort="high")
        self.assertEqual(post.call_args.kwargs["json"]["reasoning_effort"], "high")

    def test_node_offers_key_and_reasoning_widgets(self):
        optional = self.node.INPUT_TYPES()["optional"]
        self.assertEqual(optional["api_key"][0], "STRING")
        self.assertEqual(optional["reasoning_effort"][0], ["off", "low", "medium", "high", "xhigh"])

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "env-secret"})
    @patch("requests.post")
    def test_invalid_reasoning_mode_is_rejected_before_request(self, post):
        with self.assertRaises(ValueError):
            self.node.enhance(**self.inputs, reasoning_effort="arbitrary")
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
