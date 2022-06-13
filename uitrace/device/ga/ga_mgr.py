import json
import os
import re
import sys
import time
import socket
import xmltodict
from uitrace.utils.param import RunMode, OSType, DriverType
from uitrace.utils.env import DeviceEnv
from uitrace.utils.toolkit import get_free_ports


class GA(object):
    def __init__(self):
        self.unity_driver = None
        self.ue_driver = None

    @property
    def unity(self):
        if not self.unity_driver:
            driver = GADriver()
            driver.start_driver(port=None, os_type=DeviceEnv.os_type, engine_type=DriverType.GA_UNITY,
                                mode=DeviceEnv.run_mode)
            self.unity_driver = driver
        return self.unity_driver

    @unity.setter
    def unity(self, driver):
        self.unity_driver = driver

    @property
    def ue(self):
        if not self.ue_driver:
            driver = GADriver()
            driver.start_driver(port=None, os_type=DeviceEnv.os_type, engine_type=DriverType.GA_UE,
                                mode=DeviceEnv.run_mode)
            self.ue_driver = driver
        return self.ue_driver

    @ue.setter
    def ue(self, driver):
        self.ue_driver = driver


ga_driver = GA()


class GADriver():
    def __init__(self):
        self.driver = None
        self.mode = None
        self.Element = None
        self.forward_prc = None

    def start_driver(self, ip="localhost", port=8200, os_type=OSType.ANDROID, engine_type=DriverType.GA_UNITY,
                     mode=RunMode.SINGLE):
        self.port = port if port else get_free_ports(1)[0]
        self.engine_type = engine_type

        if os_type == OSType.IOS:
            # DeviceEnv.dev_mgr.cmd_tid(["relay", str(self.port), "27019"])
            if mode == RunMode.CLOUDTEST:
                self.forward_prc = DeviceEnv.dev_mgr.iproxy_port(self.port, 27019)
            else:
                self.forward_prc = DeviceEnv.dev_mgr.forward_port(self.port, 27019)
            time.sleep(1)
            sys.path.append(os.path.join(os.path.dirname(__file__), "GAutomatorIOS"))
            from ga2.engine.element import Element
            self.Element = Element
            if self.engine_type == DriverType.GA_UNITY:
                from ga2.engine.unityEngine import UnityEngine
                self.driver = UnityEngine(ip, self.port)
            elif self.engine_type == DriverType.GA_UE:
                from ga2.engine.UE4Engine import UE4Engine
                self.driver = UE4Engine(ip, self.port)
        elif os_type == OSType.ANDROID:
            self.forward_prc = DeviceEnv.dev_mgr.cmd_adb(["forward", "tcp:" + str(self.port), "tcp:27019"])
            time.sleep(0.5)
            sys.path.append(os.path.join(os.path.dirname(__file__), "GAutomatorAndroid"))
            from wpyscripts.wetest.element import Element
            self.Element = Element
            if self.engine_type == DriverType.GA_UNITY:
                from wpyscripts.wetest.engine import UnityEngine
                self.driver = UnityEngine(ip, self.port, None)
            elif self.engine_type == DriverType.GA_UE:
                from wpyscripts.wetest.engine import UnRealEngine
                self.driver = UnRealEngine(ip, self.port, None)

    def stop_driver(self):
        try:
            if self.driver is not None:
                self.driver.socket.socket.shutdown(socket.SHUT_RDWR)
                self.driver.socket.close()
                self.driver = None
        except Exception:
            pass
        try:
            if self.forward_prc is not None:
                self.forward_prc.kill()
                # os.kill(self.forward_prc.pid, signal.SIGTERM)
                self.forward_prc = None
        except:
            pass

    def unity_xml(self):
        xml = self.driver._get_dump_tree()["xml"]
        ctrl_tree = xmltodict.parse(xml, encoding='utf-8')
        path_dict = {}

        def dict_walk(ctrl_tree, path=""):
            if "GameObject" in ctrl_tree.keys():
                if not isinstance(ctrl_tree["GameObject"], list):
                    ctrl_tree["GameObject"] = [ctrl_tree["GameObject"]]
                num = len(ctrl_tree["GameObject"])
                for i in range(num):
                    cur_path = path + "/" + ctrl_tree["GameObject"][i]["@name"]
                    if cur_path not in path_dict:
                        path_dict[cur_path] = 0
                    path_count = path_dict[cur_path]
                    path_dict[cur_path] += 1
                    if path_count > 0:
                        cur_path = cur_path + ("[%d]" % path_count)
                    ctrl_tree["GameObject"][i]["@path"] = cur_path
                    # element = self.driver.find_element(cur_path)
                    # if element:
                    element = self.Element(ctrl_tree["GameObject"][i]["@path"], int(ctrl_tree["GameObject"][i]["@id"]))
                    bound = self.driver.get_element_bound(element)
                    if bound:
                        ctrl_tree["GameObject"][i]["@position"] = {
                            "x": bound.x,
                            "y": bound.y,
                            "width": bound.width,
                            "height": bound.height,
                            "visible": bound.visible
                        }
                    dict_walk(ctrl_tree["GameObject"][i], cur_path)
            return ctrl_tree
        return dict_walk(list(ctrl_tree.values())[0])

    def ue_xml(self):
        xml = self.driver._get_dump_tree()["xml"]
        ctrl_tree = xmltodict.parse(xml, encoding='utf-8')

        def dict_walk(ctrl_tree):
            if "UWidget" in ctrl_tree.keys():
                if not isinstance(ctrl_tree["UWidget"], list):
                    ctrl_tree["UWidget"] = [ctrl_tree["UWidget"]]
                num = len(ctrl_tree["UWidget"])
                for i in range(num):
                    element = self.Element(ctrl_tree["UWidget"][i]["@name"], int(ctrl_tree["UWidget"][i]["@id"]))
                    bound = self.driver.get_element_bound(element)
                    if bound:
                        ctrl_tree["UWidget"][i]["@position"] = {
                            "x": bound.x,
                            "y": bound.y,
                            "width": bound.width,
                            "height": bound.height,
                            "visible": bound.visible
                        }
                    dict_walk(ctrl_tree["UWidget"][i])
            return ctrl_tree

        return dict_walk(list(ctrl_tree.values())[0])

    def xml_handler(self):
        if self.engine_type == DriverType.GA_UNITY:
            return self.unity_xml()
        if self.engine_type == DriverType.GA_UE:
            return self.ue_xml()

    def get_uitree(self):
        return self.xml_handler()

    # def get_pos(self, name):
    #     try:
    #         m = re.search(r"^(.*?)\[@id=(.*?)\]$", name.strip())
    #         id = ""
    #         if m is not None:
    #             name = m.group(1)
    #             id = m.group(2)
    #         if "find_elements_path" in self.driver:
    #             elements = self.driver.find_elements_path(name)
    #             if elements is None or len(elements) == 0:
    #                 return None
    #             for element in elements:
    #                 if id == "" or str(element.instance) == id:
    #                     bound = self.get_element_bound(element)
    #                     return [bound.x+bound.width/2, bound.y+bound.height/2]
    #         else:
    #             element = self.driver.find_element(name)
    #             if element is not None:
    #                 bound = self.driver.get_element_bound(element)
    #                 return [bound.x+bound.width/2, bound.y+bound.height/2]
    #     except:
    #         pass
    #     return None

    def get_pos(self, xpath):
        if self.engine_type == DriverType.GA_UNITY:
            elems = self.get_elements(xpath)
            elem = elems[0] if elems else None
        elif self.engine_type == DriverType.GA_UE:
            elem = self.driver.find_element(xpath)
        if elem:
            bound = self.driver.get_element_bound(elem)
            return [bound.x + bound.width / 2, bound.y + bound.height / 2]
        return None

    def get_elements(self, xpath):
        try:
            m = re.search(r"^(.*?)\[@id=(.*?)\]$", xpath.strip())
            id = None
            if m is not None:
                xpath = m.group(1)
                id = m.group(2)

            elements = self.driver.find_elements_path(xpath)
            if not elements:
                return None
            if not id:
                return elements
            for elem in elements:
                if str(elem.instance) == id:
                    return [elem]
            return elements
        except:
            pass
        return None
