import os
from seldom.logging import log
from seldom.har2case import utils


class HarParser(object):

    def __init__(self, har_file_path):
        self.har_file_path = har_file_path
        self.case_template = """import seldom


class TestRequest(seldom.TestCase):

    def start(self):
        self.url = "{url}"

    def test_case(self):
        headers = {header}
        cookies = {cookie}
        self.{method}(self.url, {params}, headers=headers, cookies=cookies)
        self.assertStatusCode({resp_status})


if __name__ == '__main__':
    seldom.main()
"""

    def _make_testcase(self):
        """
        make test case.
        test case are parsed from HAR log entries list.
        """
        testcase = ""
        log_entries = utils.load_har_log_entries(self.har_file_path)

        for entry_json in log_entries:
            url = entry_json["request"].get("url")
            method = entry_json["request"].get("method").lower()
            headers = entry_json["request"].get("headers")
            cookies = entry_json["request"].get("cookies")

            response_status = entry_json["response"].get("status")

            headers_str = utils.list_to_dict_str(headers)
            cookies_str = utils.list_to_dict_str(cookies)
            if "?" in url:
                url = url.split("?")[0]

            data_str = ""
            if method == "post" or method == "put" or method == "delete":
                # from-data
                params = entry_json["request"]["postData"].get("params")
                if params is not None:
                    params_dict = utils.list_to_dict_str(params)
                    data_str = "data=" + params_dict
                else:
                    data_str = "data={}"
                # json
                text = entry_json["request"]["postData"].get("text")
                mime_type = entry_json["request"]["postData"].get("mimeType")
                if mime_type is not None:
                    if mime_type == "application/json":
                        data_str = "json=" + text
                else:
                    data_str = "json={}"

            elif method == "get":
                # params
                query_string = entry_json["request"].get("queryString")
                if query_string is not None:
                    query_string_str = utils.list_to_dict_str(query_string)
                    data_str = "params=" + query_string_str
                else:
                    data_str = "params={}"
            else:
                raise TypeError("Only POST/GET/PUT/DELETE methods are supported。")

            testcase = self.case_template.format(header=headers_str,
                                                 cookie=cookies_str,
                                                 method=method,
                                                 url=url,
                                                 params=data_str,
                                                 resp_status=response_status)

        return testcase

    def create_file(self, save_path, file_content=""):
        """
        create test case file
        """
        with open(save_path, 'w') as f:
            f.write(file_content)
        msg = "created file: {}".format(save_path)
        log.info(msg)

    def gen_testcase(self):
        har_file = os.path.splitext(self.har_file_path)[0]
        output_testcase_file = "{}.py".format(har_file)
        log.info(output_testcase_file)

        log.info("Start to generate testcase.")
        testcase = self._make_testcase()

        har_path = os.path.dirname(os.path.abspath(har_file))
        self.create_file(os.path.join(har_path, output_testcase_file), testcase)


if __name__ == '__main__':
    hp = HarParser("./demo.har")
    hp.gen_testcase()

