from testindata.TDA import TDA
from pascal_voc_tools import PascalXml
import os
import json
import xml

class CliUpload():
    def __init__(self, tda:TDA,  conf):
        self.tda = tda
        self.config = conf
        if conf['format'] not in ["voc", "coco", "customize"]:
            conf['format'] = "customize"

        self.format = conf['format']

        if not self.config['path']:
            raise Exception("you should specify where your files are!")


    def __VocAddFiles(self):
        """
        voc数据解析和AddFile
        :return:
        """

        if not self.config['apath']:
            raise Exception("you should specify where your annotation files are, when you set format to voc or coco")

        fileAndAnn = {}
        kList = {}
        if self.config['path']:
            for root, dirs, files in os.walk(self.config['path']):
                for filename in files:
                    if filename.endswith(tuple(self.config['fe'])):
                        fpath = os.path.join(root, filename)
                        k = "".join(fpath.replace(self.config['path'], "").split(".")[:-1]).lstrip("/").lstrip("\\")
                        kList[k] = fpath

        vList = {}
        if self.config['apath']:
            for root, dirs, files in os.walk(self.config['apath']):
                for filename in files:
                    if filename.endswith(tuple(self.config['afe'])):
                        annPath = os.path.join(root, filename)
                        v = "".join(annPath.replace(self.config['apath'], "").split(".")[:-1]).lstrip("/").lstrip("\\")
                        vList[v] = annPath


        for name, path in kList.items():
            fileAndAnn[kList[name]] = vList[name]


        for filePath, annPath in fileAndAnn.items():
            fileMetaData = {
                "format":self.format,
                "type":"file"
            }

            objectName = filePath.replace(self.config['path'], "").strip("/").strip("\\")
            f = self.tda.AddFile(filePath, objectName=objectName, metaData=fileMetaData)

            x = PascalXml()
            x.load(annPath)
            for obj in x.object:
                box = {
                    "x":obj.bndbox.xmin,
                    "y":obj.bndbox.ymin,
                    "width":obj.bndbox.xmax - obj.bndbox.xmin,
                    "height":obj.bndbox.ymax - obj.bndbox.ymin
                }

                attrs = {
                    "pose":obj.pose,
                    "truncated":obj.truncated,
                    "difficult":obj.difficult,
                }

                f.AddBox2D(box, label=obj.name, attrs=attrs)

            annMetaData = {
                "format":self.format,
                "type":"annotation"
            }

            annObjectName = annPath.replace(self.config['apath'], "").strip("/").strip("\\")
            self.tda.AddFile(annPath, objectName=annObjectName, metaData=annMetaData)


    def __CoCoAddFiles(self):pass

    def __DefaultAddFiles(self):
        filePathList = []
        if self.config['path']:
            for root, dirs, files in os.walk(self.config['path']):
                for filename in files:
                    if filename.endswith(tuple(self.config['fe'])):
                        fpath = os.path.join(root, filename)
                        filePathList.append(fpath)

        annPathList = []
        if self.config['apath']:
            for root, dirs, files in os.walk(self.config['apath']):
                for filename in files:
                    if filename.endswith(tuple(self.config['afe'])):
                        annPath = os.path.join(root, filename)
                        annPathList.append(annPath)

        for fpath in filePathList:
            fileMetaData = {
                "type":"file"
            }
            objectName = fpath.replace(self.config['path'], "").strip("/").strip("\\")
            self.tda.AddFile(fpath, objectName=objectName, metaData=fileMetaData)

        for apath in annPathList:
            fileMetaData = {
                "type":"annotation"
            }
            objectName = apath.replace(self.config['apath'], "").strip("/").strip("\\")
            self.tda.AddFile(apath, objectName=objectName, metaData=fileMetaData)

    def AddFiles(self):
        """
        :return:
        """
        if self.format == "voc":
            self.__VocAddFiles()
        elif self.format == "coco":
            self.__DefaultAddFiles()
        else:
            self.__DefaultAddFiles()




