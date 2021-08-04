import click
import json
import os
import requests
import testindata
import shutil
from testindata.cli import account
from testindata.cli.cliUpload import CliUpload

from testindata.TDA import TDA
from testindata.utils import util


def _download(url, savePath):
    res = requests.get(url)
    saveDir = os.path.split(savePath)[0]
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    with open(savePath, 'wb') as f:
        f.write(res.content)

def printVersion(ctx):
    if hasattr(testindata, "VERSION"):
        click.echo("")
        click.echo(".___________. _______       ___      ")
        click.echo("|           ||       \     /   \     ")
        click.echo("`---|  |----`|  .--.  |   /  ^  \    ")
        click.echo("    |  |     |  |  |  |  /  /_\  \   ")
        click.echo("    |  |     |  '--'  | /  _____  \  ")
        click.echo("    |__|     |_______/ /__/     \__\ ")
        click.echo("")
        click.echo(f'    TDA Version {testindata.VERSION}')
        click.echo('    more about: http://ai.testin.cn/')
        click.echo('    login: https://dataset.testin.cn/')
        click.echo("")
        ctx.exit()
    click.echo('TDA Version 0.0.1')
    ctx.exit()


@click.group()
@click.option("-ak", "--accessKey", 'access_key', default="", help="access key to Testin dataset system, see: https://dataset.testin.cn/accesskey")
@click.option("-host", "--host", 'host', default="https://dataset.testin.cn/", help="domain name that access to dataset system you would like to operate, default will be: https://dataset.testin.cn/")
@click.option('--debug/--no-debug', default=True, help="using debug mod or not, default is False")
@click.pass_context
def main(ctx, access_key, host, debug):
    """
    testin dataset system management tool
    """
    info = {
        "access_key": access_key,
        "host": host,
        "DEBUG": debug
    }

    _tda = None

    if access_key == "":
        configFile = account._config_filepath()
        if os.path.exists(configFile):
            with open(configFile, "r", encoding="utf-8") as cf:
                if cf.read() != "":
                    info = account._getConf()
                    info["DEBUG"] = debug

    if info["access_key"] != "":
        _tda = TDA(info["access_key"], info["host"])
        if info["DEBUG"]:
            _tda.Debug()

    ctx.obj = _tda


@main.command()
@click.pass_context
def version(ctx):
    """ show version """
    printVersion(ctx)
    ctx.exit()


@main.command()
@click.option("-ak", "--accessKey", 'access_key', default="", help="access key to Testin dataset system, see: https://dataset.testin.cn/accesskey")
@click.option("-h", "--host", 'host', default="https://dataset.testin.cn/", help="domain name that access to dataset system you would like to operate, default will be: https://dataset.testin.cn/")
def config(access_key, host):
    """ setting your account """
    configFile = account._config_filepath()
    if access_key == "":
        if account._check():
            click.echo("account:")
            print(account._getConf())
            exit()
    else:
        conf = {
            "access_key": access_key,
            "host": host,
        }
        with open(configFile, "w") as config:
            json.dump(conf, config)
            click.echo("config success")
            print(conf)
            exit()

@main.command()
@click.option("-ds", "--datasetId", 'ds_id', default="", help="the dataset you wolud like to download")
@click.option("-save", "--saveDir", 'save_dir', default="", help="save path for downloaded files")
@click.pass_context
def download(ctx, ds_id, save_dir):
    """ download dataset data """
    if ctx.obj == None:
        account._noLoginMessage()

    ctx.obj.SetDataset(ds_id)
    saveDir = os.path.join(save_dir, ds_id)
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    page = 0
    limit = 100
    fileTotal = 1
    while True:
        offset = page * limit
        fileData = ctx.obj.GetData(offset, limit)
        if len(fileData["files"]) <= 0:
            break
        page += 1
        for file in fileData["files"]:
            picPath = file.path.split(ds_id)[1].strip("/")
            basename = os.path.basename(picPath)
            tmpPath = picPath.replace(basename, "").strip("/")

            fileDir = os.path.join(saveDir, tmpPath)
            if not os.path.exists(fileDir):
                os.makedirs(fileDir)

            filePath = os.path.join(fileDir, tmpPath, basename)
            if os.path.exists(filePath):
                fmd5 = util.getFileMd5(filePath)
                if fmd5 != file.md5:
                    _download(file.url, filePath)
                    if ctx.obj.debug:
                        print(f"[SAVE_FILE]file total: {fileTotal}, truncate file, redo: [{filePath}]")
                else:
                    if ctx.obj.debug:
                        print(f"[SAVE_FILE]file total: {fileTotal}, file already exist: [{filePath}]")
            else:
                _download(file.url, filePath)
                if ctx.obj.debug:
                    print(f"[SAVE_FILE]file total: {fileTotal}, file download and save: [{filePath}]")

            labelData = ctx.obj.GetFileAndLabel(fid=file.fid)
            jsonname = ".".join(basename.split(".")[:-1])
            jsonPath = os.path.join(fileDir, tmpPath, jsonname + "_label.json")
            with open(jsonPath, "w", encoding="utf-8") as jf:
                json.dump(labelData.anotations.labels, jf)
                if ctx.obj.debug:
                    print(f"[SAVE_LABEL]file total: {fileTotal}, save label data: [{jsonPath}]")

            fileTotal += 1

    if ctx.obj.debug:
        print("done!")

@main.command()
@click.pass_context
def clearcache(ctx):
    """ clean up the SDK caches """
    dir = os.path.split(account._config_filepath())[0]
    shutil.rmtree(dir)
    click.echo("all caches are cleaned up! :)")
    exit()


#从已有的数据集中加载数据到数据集管理系统
@main.command()
@click.option("-format", "--format", 'format', default="customize", help="your uploading-data format, default:voc")
@click.option("-fp", "--file-path", 'path', type=click.Path(exists=True), help="your uploading-data path")
@click.option("-fe", "--file-extension", 'fe', default=[""], help="your uploading-data file extension name")
@click.option("-afp", "--annotation-file-path", 'apath', type=click.Path(exists=True), help="your annotation file path")
@click.option("-at", "--annotation-type", 'at', default="xml", help="your annotation file content type: xml、json etc.")
@click.option("-afe", "--annotation-extension", 'afe', default=[""], help="your annotation file extension name")
@click.option("-ds", "--datasetId", 'ds_id', default="", help="the dataset you wolud like to upload")
@click.pass_context
def upload(ctx, format, path, fe, apath, at, afe, ds_id):
    """
    upload standard format data to testin dataset system
    """
    if not path:
        click.echo("you should specify where your files are!")
        click.echo("")
        click.echo("    use option -fp or --file-path to set your file path")
        click.echo("")
        ctx.exit()



    if (not apath) and (format in ["voc", "coco"]):
        click.echo("you should specify where your annotation files are, when you set format to voc or coco")
        click.echo("")
        click.echo("    use option -ds or --datasetId to set your dataset ID")
        click.echo("")
        ctx.exit()


    if not ds_id:
        click.echo("you should specify the dataset you would like to upload")
        click.echo("")
        click.echo("    use option -afp or --annotation-file-path to set your annotation file path")
        click.echo("")
        ctx.exit()

    ctx.obj.SetDataset(ds_id)


    conf = {
        "format":format,
        "path":path,
        "fe":fe,
        "apath":apath,
        "at":at,
        "afe":afe,
        "ds_id":ds_id,
    }

    up = CliUpload(ctx.obj, conf)
    up.AddFiles()

    ctx.obj.Upload()
    ctx.exit()




if __name__ == '__main__':
    main(obj={})



