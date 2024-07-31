import json
import unittest

from arelight.run.infer import create_infer_parser

from utils import do_format, extract


class TestArgumentsReader(unittest.TestCase):

    def test(self):
        infer_parser = create_infer_parser()
        infer_schema = extract(infer_parser)
        print(json.dumps(infer_schema, indent=4))

        d = {}
        for k, v in infer_schema["schema"].items():
            d[k] = do_format(v, is_check=False)
        print(d)
