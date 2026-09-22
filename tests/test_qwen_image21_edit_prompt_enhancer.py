import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import torch


NODE_FILE = Path(__file__).resolve().parents[1] / "nodes" / "QwenImage21EditPromptEnhancerNode.py"
spec = importlib.util.spec_from_file_location("qwen_image21_edit_prompt_enhancer", NODE_FILE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Node = module.QwenImage21EditPromptEnhancerNode


class QwenImage21EditPromptEnhancerTests(unittest.TestCase):
    def setUp(self):
        self.node = Node()
        self.inputs = dict(
            prompt="把背景改成蓝色，人物保持不变",
            images=torch.ones((1, 16, 24, 3), dtype=torch.float32),
            system_prompt=module.DEFAULT_EDIT_SYSTEM_PROMPT,
            model="qwen3.8-27b",
            temperature=0.7,
            max_tokens=2048,
            timeout=30,
        )

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret"})
    @patch("requests.post")
    def test_image_is_sent_and_json_outputs_are_separate(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content":
            '{"rewritten_prompt":"将图像背景改为均匀蓝色，人物与构图保持不变。","wh_ratio":"","ratio_follow":"<image1>"}'}}]})
        result = self.node.enhance(**self.inputs)
        self.assertEqual(result, ("将图像背景改为均匀蓝色，人物与构图保持不变。", "", "<image1>"))
        payload = post.call_args.kwargs["json"]
        parts = payload["messages"][1]["content"]
        self.assertEqual(parts[0], {"type": "text", "text": self.inputs["prompt"]})
        self.assertTrue(parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(payload["reasoning_effort"], "medium")

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret"})
    @patch("requests.post")
    def test_multiple_images_keep_order(self, post):
        self.inputs["images"] = torch.stack((torch.zeros((16, 24, 3)), torch.ones((16, 24, 3))))
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content":
            '{"rewritten_prompt":"将<image1>的人物放入<image2>的背景。","wh_ratio":"","ratio_follow":"<image2>"}'}}]})
        result = self.node.enhance(**self.inputs)
        self.assertEqual(result[2], "<image2>")
        parts = post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertEqual(len(parts), 3)
        self.assertNotEqual(parts[1]["image_url"]["url"], parts[2]["image_url"]["url"])

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret"})
    @patch("requests.post")
    def test_invalid_json_does_not_bypass_rewrite(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content": "not json"}}]})
        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            self.node.enhance(**self.inputs)

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": "test-secret"})
    @patch("requests.post")
    def test_inconsistent_ratio_is_rejected(self, post):
        post.return_value = Mock(status_code=200, json=lambda: {"choices": [{"message": {"content":
            '{"rewritten_prompt":"Edit.","wh_ratio":"16:9","ratio_follow":"<image1>"}'}}]})
        with self.assertRaisesRegex(RuntimeError, "inconsistent"):
            self.node.enhance(**self.inputs)

    @patch.dict(os.environ, {"ZMG_GPUSTACK_API_KEY": ""})
    def test_missing_key_is_not_ignored(self):
        with self.assertRaisesRegex(RuntimeError, "API Key"):
            self.node.enhance(**self.inputs)


if __name__ == "__main__":
    unittest.main()
