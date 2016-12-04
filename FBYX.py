#-------------------------------------------------------------------------------
# Name:        FBYX
# Purpose:
#
# Author:      LIRIAN
#
# Created:     10/11/2016
#
#11月21日增加华泰界面交易
#11月29日增加日志文件，增加关闭窗口保存全局变量，增加选股策略全局变量，增加显示当日选股按钮
#-------------------------------------------------------------------------------
###################################################选股策略全局变量#####################################################################
ASK_ALL_BID_ALL_RATE = 1.2  # 总买 >= ASK_ALL_BID_ALL_RATE  * 总卖:
NOW_HIGH_RATE = 1.002       # 现价 * NOW_HIGH_RATE 〉最高价
ZF_MX = 4.0                 # 涨幅门限
LB_MX_BEFORE_10 = 3         # 量比门限10点之前
LB_MX_AFTER_10 = 1          # 量比门限10点之后
########################################################################################################################
g_Account = ''     # 在引号里填写，不要去掉引号
g_trade_Secr = ''
g_network_serc = ''
MAX_BUY_STOCKS = 3 # 最多买3只股票
########################################################################################################################
import datetime
import wx
import tushare as ts
import pandas as pd
import os
import time
import sqlite3
import threading
import pickle
import sys
THREAD_RUNNING = False
G_MINUTE_RCD_TUPLE = None
G_SELECT_STOCK_RCD_LOG = ''
########################################################################################################################
from win32gui import *
import win32gui
import win32api
import win32con
import win32process
from commctrl import TVM_GETITEMHEIGHT,TVM_GETCOUNT
from commctrl import TVM_GETNEXTITEM ,TVGN_LASTVISIBLE,TVGN_CARET,TVM_SELECTITEM,TVGN_PREVIOUS,LVM_GETITEMCOUNT,TVGN_FIRSTVISIBLE
title_ht=u'网上股票交易系统5.0'
Hwnd_BuyEidt_Dlg=0
Hwnd_StockCode_Eidt=0
Hwnd_BuyPrice_Eidt=0
Hwnd_BuyNum_Eidt=0
Hwnd_Buy_Btn=0
MainWinList = []
MAX_BUY_THREAD = 0
StopATbuy = False
########################################################################################################################
__GPATH__=os.path.split(os.path.realpath(__file__))[0]
DATA= 'bigdata'
PATH_ALL_STOCK_NAME=__GPATH__+ os.sep +DATA +os.sep+'AllStockCode.csv'
PATH_SELF_STOCK_NAME=__GPATH__+ os.sep +DATA +os.sep+'SelfStockCode.csv'
PATH_STOCK_HIS_DATA=__GPATH__+ os.sep +DATA +os.sep+'StockHisData'
PATH_DATABASE=__GPATH__+ os.sep +DATA +os.sep+time.strftime("%Y%m%d",time.localtime(time.time()))+ 'hq_'
PATH_SELETC_LIST=__GPATH__+ os.sep +DATA +os.sep+time.strftime("%Y%m%d",time.localtime(time.time()))+'SELETC.LIST'
PATH_ONE_MINUTE=__GPATH__+ os.sep +DATA +os.sep+time.strftime("%Y%m%d",time.localtime(time.time()))+'one_minute_vol.rcd'
PATH_BUY_STOCK_TODAY = __GPATH__+ os.sep +DATA +os.sep+time.strftime("%Y%m%d",time.localtime(time.time()))+'buy_ed_stocks.tody' # 已经买入的股票
PATH_BUY_SELECT_STOCK = __GPATH__+ os.sep +DATA +os.sep+time.strftime("%Y%m%d",time.localtime(time.time()))+'buy_stocks.slect' # 被选入即将买的股票
PATH_LOG_FILE = __GPATH__+ os.sep +DATA +os.sep+time.strftime("%Y%m%d",time.localtime(time.time()))+'log.txt' # 被选入即将买的股票
########################################################################################################################
SHOW_SQL = False



def fetch_data_from_stock_table(conn,tableName):
    #'''查询所有数据...'''
    #print('查询一只股票所有数据...')
    fetchall_sql = '''SELECT * FROM ''' +tableName
    return  fetchall(conn, fetchall_sql)

def fetchall(conn, sql):
    r = []
    if sql is not None and sql != '':
        cu = get_cursor(conn)
        #if SHOW_SQL:
            #print('执行sql:[{}]'.format(sql))
        cu.execute(sql)
        r = cu.fetchall()
        """if len(r) > 0:
            for e in range(len(r)):
                print(r[e])"""
        close_all(conn,cu)
    else:
        print('the [{}] is empty or equal None!'.format(sql))
    return r




def get_conn(path):
    conn = sqlite3.connect(path)
    if os.path.exists(path) and os.path.isfile(path):
        #print('硬盘上面:[{}]'.format(path))
        return conn
    else:
        conn = None
        print('内存上面:[:memory:]')
        return sqlite3.connect(':memory:')


def get_cursor(conn):
    if conn is not None:
        return conn.cursor()
    else:
        return get_conn('').cursor()

def close_all(conn, cu):
        '''关闭数据库游标对象和数据库连接对象'''
        try:
            if cu is not None:
                cu.close()
        finally:
            if cu is not None:
                cu.close()
########################################################################################################################
class MyFrame2(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"==翻倍量化选股==", pos=wx.DefaultPosition,
                          size=wx.Size(1600, 900),
                          style=wx.DEFAULT_FRAME_STYLE | wx.HSCROLL | wx.TAB_TRAVERSAL | wx.VSCROLL, name=u"QDAPP")

        #self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)
        self.RUNNING_READ_DB = 0

        bSizer1 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_panel2 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(-1, -1), wx.TAB_TRAVERSAL)
        self.m_panel2.SetMaxSize(wx.Size(200, -1))

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.m_button14 = wx.Button(self.m_panel2, wx.ID_ANY, u"获取沪深股票列表", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button14, 0, wx.ALL, 15)

        self.m_button11 = wx.Button(self.m_panel2, wx.ID_ANY, u"获取历史数据", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button11, 0, wx.ALL, 15)

        self.m_staticText2 = wx.StaticText(self.m_panel2, wx.ID_ANY, u"DZH路径：", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        bSizer2.Add(self.m_staticText2, 0, wx.ALIGN_LEFT, 10)

        self.m_textCtrl3 = wx.TextCtrl(self.m_panel2, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(200, -1),
                                       0)
        bSizer2.Add(self.m_textCtrl3, 0, wx.ALL, 5)

        self.m_button99 = wx.Button(self.m_panel2, wx.ID_ANY, u"SAVE路径", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button99, 0, wx.ALL, 15)

        self.m_button10 = wx.Button(self.m_panel2, wx.ID_ANY, u"获取DZH自选股", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button10, 0, wx.ALL, 15)

        self.m_button101 = wx.Button(self.m_panel2, wx.ID_ANY, u"显示DZH自选股", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button101, 0, wx.ALL, 15)
        self.m_button101.Hide()

        self.m_button15 = wx.Button(self.m_panel2, wx.ID_ANY, u"NONE", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button15.Hide()

        bSizer2.Add(self.m_button15, 0, wx.ALL, 15)

        self.m_button121 = wx.Button(self.m_panel2, wx.ID_ANY, u"检测数据库", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button121, 0, wx.ALL, 15)

        self.m_button151 = wx.Button(self.m_panel2, wx.ID_ANY, u"启动读取数据库", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button151, 0, wx.ALL, 15)

        #self.m_button12 = wx.Button(self.m_panel2, wx.ID_ANY, u"停止读取", wx.DefaultPosition, wx.DefaultSize, 0)
        #bSizer2.Add(self.m_button12, 0, wx.ALL, 15)



        self.m_button13 = wx.Button(self.m_panel2, wx.ID_ANY, u"显示当日入选股", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button13, 0, wx.ALL, 15)

        self.m_button1300 = wx.Button(self.m_panel2, wx.ID_ANY, u"显示所有入选股", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button1300,0, wx.ALL, 15)

        self.m_button131 = wx.Button(self.m_panel2, wx.ID_ANY, u"启动HT界面获取句柄", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button131, 0, wx.ALL, 15)

        self.m_button1311 = wx.Button(self.m_panel2, wx.ID_ANY, u"停止HT交易", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button1311, 0, wx.ALL, 15)

        self.m_panel2.SetSizer(bSizer2)
        self.m_panel2.Layout()
        bSizer2.Fit(self.m_panel2)
        bSizer1.Add(self.m_panel2, 1, wx.ALL | wx.EXPAND, 1)

        self.m_panel3 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(-1, -1), wx.TAB_TRAVERSAL)
        bSizer3 = wx.BoxSizer(wx.VERTICAL)
        self.listcontrl = wx.ListCtrl(self.m_panel3, -1, style=wx.LC_REPORT)
        #self.m_scrolledWindow1 = wx.ScrolledWindow(self.m_panel3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,wx.HSCROLL | wx.VSCROLL)

        #self.m_scrolledWindow1.SetScrollRate(5, 5)
        bSizer3.Add(self.listcontrl, 1, wx.EXPAND | wx.ALL, 5)






        self.m_textCtrl16 = wx.TextCtrl(self.m_panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, 150),
                                        wx.TE_MULTILINE | wx.VSCROLL)
        bSizer3.Add(self.m_textCtrl16, 0, wx.ALIGN_BOTTOM | wx.ALL | wx.EXPAND, 5)

        self.m_panel3.SetSizer(bSizer3)
        self.m_panel3.Layout()
        bSizer3.Fit(self.m_panel3)
        bSizer1.Add(self.m_panel3, 1, wx.ALL | wx.EXPAND, 1)

        self.SetSizer(bSizer1)
        self.Layout()
        #self.m_statusBar1 = self.CreateStatusBar(1, wx.ST_SIZEGRIP, wx.ID_ANY)
        self.m_toolBar1 = self.CreateToolBar(wx.TB_HORIZONTAL, wx.ID_ANY)
        self.m_toolBar1.Realize()

        self.Centre(wx.BOTH)

        # Connect Events
        self.m_button10.Bind(wx.EVT_LEFT_DOWN, self.onGetStockList)
        self.m_button101.Bind(wx.EVT_LEFT_DOWN, self.onShowStockList)
        self.m_button11.Bind(wx.EVT_LEFT_DOWN, self.onGetStockHisData)
        self.m_button99.Bind(wx.EVT_LEFT_DOWN, self.onSavePath)
        #self.m_button12.Bind(wx.EVT_LEFT_DOWN, self.onStop)
        self.m_button121.Bind(wx.EVT_LEFT_DOWN, self.onCheckDatabase)
        self.m_button13.Bind(wx.EVT_LEFT_DOWN, self.onShowMoniterResult)
        self.m_button1300.Bind(wx.EVT_LEFT_DOWN, self.onShowAllMoniterResult)
        self.m_button131.Bind(wx.EVT_LEFT_DOWN, self.onStartHTtrading)
        self.m_button1311.Bind(wx.EVT_LEFT_DOWN, self.onStopHTtrading)
        self.m_button14.Bind(wx.EVT_LEFT_DOWN, self.onGetAllStockList)
        self.m_button151.Bind(wx.EVT_LEFT_DOWN, self.onRun)


        #TODO
        self.ShowPath()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        WrieTxtLogFile('start window gui')

    def OnClose(self, event):
        global THREAD_RUNNING
        THREAD_RUNNING = False
        ret = wx.MessageBox('请麻烦点确认，保存全局变量', 'Confirm', wx.OK)
        if ret == wx.OK:
            if G_MINUTE_RCD_TUPLE != None:  # 5分钟存档一次我要保存全局变量
                try:
                    dumpdata(PATH_ONE_MINUTE, G_MINUTE_RCD_TUPLE)
                except Exception as e:
                    print(e)
            print("close window gui")
            WrieTxtLogFile('close window')
        event.Skip()
    def __del__(self):
        pass

    def ShowPath(self):
        newconfig = os.path.split(os.path.realpath(__file__))[0] + os.sep  + DATA+ os.sep+ 'conf.ini'
        if os.path.exists(newconfig):
            pkl_file = open(newconfig, 'rb')
            savedic = pickle.load(pkl_file)
            path = savedic['path'].decode("gbk")
            self.m_textCtrl3.SetValue(path)


    def onSavePath(self, event):
        path = self.m_textCtrl3.GetValue()
        newconfig = os.path.split(os.path.realpath(__file__))[0] + os.sep + DATA+ os.sep + 'conf.ini'
        if os.path.exists(newconfig):
            os.remove(newconfig)
        output = open(newconfig, 'wb')
        savedic = {}
        savedic['path'] = path.encode("gbk")
        pickle.dump(savedic, output)
        output.close()
        event.Skip()

    # Virtual event handlers, overide them in your derived class
    def onGetStockList(self, event):
        #try:
            path  = self.m_textCtrl3.GetValue() # D:\dzh365\DZH\USERDATA\block
            print('DZD path:',path)
            self.getStockListFrmDZH(path)
        #except:
            #wx.CallAfter(frame.updateUI, updateLog=u"获取DZH自选股失败，1。请检查路径 2。代码出错")
            event.Skip()

    def onShowStockList(self, event):
        self.listcontrl.ClearAll()
        if os.path.exists(PATH_SELF_STOCK_NAME):
            df = pd.read_csv(PATH_SELF_STOCK_NAME, encoding='gbk')
            dflist =  df.values
            #print(dflist)

            if df.shape[1]<3:
                if self.listcontrl.ColumnCount<2:
                    self.listcontrl.InsertColumn(0, "index")
                    self.listcontrl.InsertColumn(1, "code")
                for item in dflist:
                    numitems = self.listcontrl.InsertItem(0,str(item[0]))
                    self.listcontrl.SetItem(numitems,1,str(item[1]).zfill(6))
            else:
                if df.shape[1]>3:
                    colm_name = df.columns
                    if self.listcontrl.ColumnCount < 2:
                        self.listcontrl.InsertColumn(0, colm_name[1])
                        self.listcontrl.InsertColumn(1, colm_name[2])
                    for item in dflist:
                        numitems= self.listcontrl.InsertItem(0, str(item[1]).zfill(6))
                        self.listcontrl.SetItem(numitems,1,str(item[2]))
            wx.CallAfter(frame.updateUI, updateLog=u"显示DZH自选股个数:%i" % (df.shape[0]))
        else:
            wx.CallAfter(frame.updateUI, updateLog=u"没有获取到股票列表文件")
        event.Skip()

    def onStartHTtrading(self,event):
        global StopATbuy
        StopATbuy =  False
        WrieTxtLogFile('onStartHTtrading')
        threading._start_new_thread(self.StartHTtrading, ())
        wx.CallAfter(frame.updateUI, updateLog=u"启动华泰自动交易程序")
        event.Skip()
    def onStopHTtrading(self,event):
        WrieTxtLogFile('onStopHTtrading')
        global StopATbuy
        StopATbuy = True
        wx.CallAfter(frame.updateUI, updateLog=u"停止自动交易!!")
        event.Skip()

    def onShowMoniterResult(self, event):
        self.ShowMoniterResult(allfile = False)
        event.Skip()

    def onShowAllMoniterResult(self, event):
        self.ShowMoniterResult()
        event.Skip()

    def onGetAllStockList(self, event):
        res = self.getAllStockCodeFrmShare()
        wx.CallAfter(frame.updateUI, updateLog=u"获取沪深股票列表完成共%i"%(res))
        event.Skip()

    def onGetStockHisData(self, event):
        WrieTxtLogFile('onGetStockHisData')
        threading._start_new_thread(self.getHisDataFrmShare,())
        wx.CallAfter(frame.updateUI, updateLog=u"后台进程获取历史数据")
        event.Skip()

    def onRun(self, event):
        global THREAD_RUNNING
        THREAD_RUNNING = True
        threading._start_new_thread(self.FILTER, ())
        self.RUNNING_READ_DB = self.RUNNING_READ_DB+1
        wx.CallAfter(frame.updateUI, updateLog=u"后台运行扫描线程个数:%i"%self.RUNNING_READ_DB)
        WrieTxtLogFile(u"后台运行扫描线程个数:%i" % self.RUNNING_READ_DB)
        event.Skip()

    def onStop(self,event):
        global THREAD_RUNNING
        THREAD_RUNNING = False
        event.Skip()
    def onCheckDatabase(self,event):
        wx.CallAfter(frame.updateUI, updateLog=u"正在后台遍历数据库，请等待")
        threading._start_new_thread(self.checkDataLen, ())
        event.Skip()

    def ShowMoniterResult(self,allfile = True,dbg = False):
        if dbg:
            onemin_rcd = pickledata(PATH_ONE_MINUTE)
            print('onemin_rcd:',onemin_rcd)
        self.listcontrl.ClearAll()
        f_list = os.listdir(__GPATH__+ os.sep +DATA)
        selectfileList = []
        for mfile in f_list:
            if os.path.splitext(mfile)[1] == '.LIST':
                if allfile == False:
                    print(mfile)
                    if mfile in PATH_SELETC_LIST:
                        selectfileList.append(mfile)
                else:
                    selectfileList.append(mfile)
        if selectfileList==[]:
            wx.CallAfter(frame.updateUI, updateLog=u"没有入选股列表文件,请关闭软件重启")
            return
        self.listcontrl.InsertColumn(0, "",width  = 2)
        self.listcontrl.InsertColumn(1, "股票代码")
        self.listcontrl.InsertColumn(2, "股票名称")
        self.listcontrl.InsertColumn(3, "入选时间",width  = 200 )

        self.listcontrl.InsertColumn(4, "入选价格")
        self.listcontrl.InsertColumn(5, "入选委比")
        self.listcontrl.InsertColumn(6, "入选涨幅")
        self.listcontrl.InsertColumn(7, "入选量比")
        self.listcontrl.InsertColumn(8, "当前价格")
        self.listcontrl.InsertColumn(9, "买入涨幅")
        self.listcontrl.InsertColumn(10, "分钟量比数")
        self.listcontrl.InsertColumn(11, "ask12")
        self.listcontrl.InsertColumn(12, "ask15")
        self.listcontrl.InsertColumn(13, "ask20")
        self.listcontrl.InsertColumn(14, "askmoney(w)",width  = 150)
        for msel in selectfileList:
            if os.path.exists(__GPATH__+ os.sep +DATA+os.sep+msel):
                pkl_file = open(__GPATH__+ os.sep +DATA+os.sep+msel, 'rb')
                mSELECT_LIST = pickle.load(pkl_file)
                pkl_file.close()
                # 股票代码，1股票名称，2入选时间，3入选价格，4入选总委比，5入选涨幅，6入选量比 ，7当前价格，8买入涨幅,9数据库名，10入选委买分钟量比,11 ask12, 12 ask15, 13 ask20, 14 ask_money
                zf_list = 0
                for item in mSELECT_LIST:
                    numitems = self.listcontrl.InsertItem(0, '')
                    self.listcontrl.SetItem(numitems, 1,str(item[0]).zfill(6))
                    self.listcontrl.SetItem(numitems, 2, str(item[1]))
                    if len(item) > 2:
                        self.listcontrl.SetItem(numitems, 3, str(item[2]))
                    if len(item) > 3:
                        self.listcontrl.SetItem(numitems, 4, str(item[3]))
                        self.listcontrl.SetItem(numitems, 5, str(item[4]))
                        self.listcontrl.SetItem(numitems, 6, str(item[5]))
                        self.listcontrl.SetItem(numitems, 7, str(item[6]))

                    if len(item)>9:
                        try:
                            dbname = item[9]
                            conn = get_conn(dbname)
                            data = fetch_data_from_stock_table(conn, item[0])
                            lastline = data[len(data)-1]
                            now = lastline[6]
                            zf = STOCK_ZF(float(item[3]),float(now))
                            self.listcontrl.SetItem(numitems, 8, str(now))
                            self.listcontrl.SetItem(numitems, 9, str(zf) )
                            zf_list = zf_list + zf
                        except Exception as e:
                            print(e)
                    if len(item)>10:
                        one_min_n = item[10]
                        self.listcontrl.SetItem(numitems, 10, str(one_min_n))
                    if len(item)>11:
                        ask12 = item[11]
                        ask15 = item[12]
                        ask20 = item[13]
                        askmoney = item[14]
                        self.listcontrl.SetItem(numitems, 11, str(ask12))
                        self.listcontrl.SetItem(numitems, 12, str(ask15))
                        self.listcontrl.SetItem(numitems, 13, str(ask20))
                        self.listcontrl.SetItem(numitems, 14, str(askmoney))


                wx.CallAfter(frame.updateUI, updateLog=u"文件%s入选股获利点:%i" % (msel, zf_list))
                wx.CallAfter(frame.updateUI, updateLog=u"显示文件%s入选股个数:%i" % (msel,len(mSELECT_LIST)))
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################
#########################################################################################################################

    def ShowCheckDatabaseResult(self,sotckdatalist):
        self.listcontrl.ClearAll()
        self.listcontrl.InsertColumn(0, "code")
        self.listcontrl.InsertColumn(1, "len")
        self.listcontrl.InsertColumn(2, "db_n")
        for item in sotckdatalist:
            numitems = self.listcontrl.InsertItem(0, str(item[0]))
            self.listcontrl.SetItem(numitems, 1, str(item[1]))
            self.listcontrl.SetItem(numitems, 2, str(item[2]))


    def getStockListFrmDZH(self,myFileStr):# 从大智慧获取自选股列表
        bakfile = open(myFileStr, 'rb')
        stockcodeList = []
        while True:
            temp0 = bakfile.read(1)
            if len(temp0) == 0:
                break
            else:
                if temp0 == 'S'.encode("gbk"):
                    temp1 = bakfile.read(1)
                    if temp1 == 'H'.encode('gbk') or temp1 == 'Z'.encode('gbk'):
                        #stockcode = temp0 + temp1
                        stockcode=b''
                        for i in range(6):
                            stockcode = stockcode + bakfile.read(1)
                        stockcodeList.append(str(stockcode,encoding='gbk'))
        bakfile.close()
        #print(stockcodeList)
        wx.CallAfter(frame.updateUI, updateLog=u"获取到DZH自选股个数:%i" % (len(stockcodeList)))
        if os.path.exists(PATH_SELF_STOCK_NAME):
            os.remove(PATH_SELF_STOCK_NAME)
        if os.path.exists(PATH_ALL_STOCK_NAME): # 获取对应的code的股票名称
            df = pd.read_csv(PATH_ALL_STOCK_NAME,encoding='gbk')
            df['code']=df['code'].astype(str)
            df['code'] = df['code'].str.zfill(6)
            dfs = df[df.loc[:,'code'].isin( stockcodeList)]
            print('zxg len:',dfs.shape[0])
            dfs.to_csv(PATH_SELF_STOCK_NAME)
        else:
            d = {'code': stockcodeList}
            df = pd.DataFrame.from_dict(data =d )
            df.to_csv(PATH_SELF_STOCK_NAME)

    #code, 代码
    #name, 名称
    #industry, 所属行业
    #area, 地区
    #pe, 市盈率
    #outstanding, 流通股本
    #totals, 总股本(万)
    #totalAssets, 总资产(万)
    #liquidAssets, 流动资产
    #fixedAssets, 固定资产
    #reserved, 公积金
    #reservedPerShare, 每股公积金
    #eps, 每股收益
    #bvps, 每股净资
    #pb, 市净率
    #timeToMarket, 上市日期

    def getAllStockCodeFrmShare(self):# 从Tushare获取两市股票列表
        stocklist = ts.get_stock_basics()
        if os.path.exists(PATH_ALL_STOCK_NAME):
            os.remove(PATH_ALL_STOCK_NAME)
        print(stocklist)
        stocklist.to_csv(PATH_ALL_STOCK_NAME )
        return len(stocklist.index)

    def getHisDataFrmShare(self):  # 从Tushare获取自选股历史数据
        try:
            if os.path.exists(PATH_SELF_STOCK_NAME):
                today = getdayStr(0)
                yestd = getdayStr(1)
                df = pd.read_csv(PATH_SELF_STOCK_NAME, encoding='gbk')
                dflist = df.values
                for j in range(len(dflist)):
                    item = dflist[j]
                    code = str(item[1]).zfill(6)
                    print("download %i: --and total:%i --and code:",(j,len(dflist),code) )
                    for i in range(1, 10):
                        try:
                            print('get_h_data : %i :' % (i))


                            hisdata = ts.get_h_data(code, start=getdayStr(i * 10),
                                                    end=today)  ################################################修改了框架的ascending = True

                            if type(hisdata) == pd.DataFrame and hisdata.shape[0] > 5:
                                hisdata['ma5_v'] = pd.rolling_mean(hisdata['volume'], 5)
                                hisdata.to_csv(PATH_STOCK_HIS_DATA + os.sep + code + '.csv')
                                break
                            else:
                                if type(hisdata) == pd.DataFrame and hisdata.shape[0] > 1:
                                    hisdata['ma5_v'] = pd.rolling_mean(hisdata['volume'], hisdata.shape[0])
                                    hisdata.to_csv(PATH_STOCK_HIS_DATA + os.sep + code + '.csv')
                                break

                                if i == 9:
                                    print(u"请删除自选股:" + code)
                                    df.drop(j)
                                    wx.CallAfter(frame.updateUI, updateLog=u"请删除自选股:" + code)
                        except Exception as e:
                            print(e)
                            if i == 9:
                                print(u"请删除自选股:" + code)
                                df.drop(j)
                                wx.CallAfter(frame.updateUI, updateLog=u"请删除自选股:" + code)
                            continue
        except Exception as e:
            print(e)
        wx.CallAfter(frame.updateUI, updateLog=u"获取历史数据结束")

    def getselfStockList(self):
        sysmbol = []
        if os.path.exists(PATH_SELF_STOCK_NAME):
            df = pd.read_csv(PATH_SELF_STOCK_NAME, encoding='gbk')
            dflist =  df.values
            for item in dflist:
                code = str(item[1]).zfill(6)
                if code[0]=='6':
                    code = 'sh'+ code
                else:
                    code = 'sz'+code
                sysmbol.append(code)
        return  sysmbol

    def updateUI(self,**kwargs):
        for key in kwargs:
            if key == 'updateLog':
                self.m_textCtrl16.AppendText(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"-->"+kwargs['updateLog']+'\n')


    def checkDataLen(self):
        #状态, PH = 盘后，PZ = 盘中，TP = 停牌, WX = 午休, LT = 临时停牌, KJ = 开盘集合竞价, PZ = 连续竞价 PQ

        ResList =[]
        sysmbol = self.getselfStockList()
        if sysmbol != []:
            print("symbol len:", len(sysmbol))
            step = 64
            symbol_list_slice = [sysmbol[i: i + step]
                                 for i in range(0, len(sysmbol), step)]
            j = 0
            for symbol_group in symbol_list_slice:
                conn = get_conn(PATH_DATABASE + str(j) + '.db')
                for stock in symbol_group:
                    try:
                        data = fetch_data_from_stock_table(conn, stock)
                    except Exception as e:
                        print(e)
                        data = []
                    if data == []:
                        ResList.append((stock,0,j))
                    else:
                        PZ_NUM=0
                        for item in data:
                            if item[7] =='PZ' :
                                PZ_NUM = PZ_NUM+1
                            if item[7] == 'TP':
                                PZ_NUM = 'TP'
                                break
                        ResList.append((stock, PZ_NUM,j))
                j = j + 1
        wx.CallAfter(self.ShowCheckDatabaseResult, ResList)
        wx.CallAfter(frame.updateUI, updateLog=u"显示结束")


    def StartHTtrading(self):
        global StopATbuy
        Account = g_Account
        trade_Secr = g_trade_Secr
        network_serc = g_network_serc
        isExistHT_flag = self.isExistHT(Account)
        if isExistHT_flag ==False:
            self.loginHT(Account,trade_Secr,network_serc)
        isExistHT_flag = self.isExistHT(Account)
        Treehwnd = 0
        if isExistHT_flag == True:
            global MainWinList
            print("MainWinList:",MainWinList)
            if len(MainWinList)>0:
                Treehwnd = getTreeHwnd(MainWinList[0])
                if Treehwnd:
                    GetBuyEidtHwnd(MainWinList[0], Treehwnd)
                    wx.CallAfter(frame.updateUI, updateLog=u"点击左侧买入,获取买入按钮句柄")









    def getSelectStock(self):
        res = []
        res = pickledata(PATH_BUY_SELECT_STOCK)
        return res



    def isExistHT(self,ht_Account):
        global MainWinList
        MainWinList = []
        windows = []
        win32gui.EnumWindows(Callback_MainWind, (windows))
        deletList = []
        #print("isExistHT function , MainWinList:",MainWinList)
        #for mitem in MainWinList:
            #if findStockzijinHwnd(mitem, ht_Account) == False:
                #deletList.append(mitem)
        for item in deletList:
            MainWinList.remove(item)
        if len(MainWinList) == 0:
            print('is not Exist HT')
            return False
        else:
            print('is Exist HT')
            return True


    def loginHT(self,Account,trade_Secr,network_serc):
        myexepath = __GPATH__ + os.sep + 'HTWT1' + os.sep + 'xiadan.exe'
        win32process.CreateProcess(myexepath, '', None, None, 0, win32process.CREATE_NO_WINDOW, None, None,
                                   win32process.STARTUPINFO())
        for i in range(5):
            LoginWinHwnd = win32gui.FindWindow(None, u'用户登录')
            if LoginWinHwnd > 0:
                break
            else:
                time.sleep(1)
        if not LoginWinHwnd > 0:
            print("---------------------------------启动失败请检:", myexepath, "---------------------")
        if LoginWinHwnd > 0:
            account_boxHwnd = win32gui.FindWindowEx(LoginWinHwnd, 0, 'ComboBox', None)
            if account_boxHwnd > 0:
                account_EditHwnd = win32gui.FindWindowEx(account_boxHwnd, 0, 'Edit', None)  # 填写 账户
                PutStr2Edit(account_EditHwnd, Account)
                time.sleep(0.1)
                Trad_Serc_Hwnd = win32gui.FindWindowEx(LoginWinHwnd, account_boxHwnd, 'Edit', None)  # 填写 交易密码
                PutStr2Edit(Trad_Serc_Hwnd, trade_Secr)
                time.sleep(0.1)
                NetWork_Serc_hwnd = win32gui.FindWindowEx(LoginWinHwnd, Trad_Serc_Hwnd, 'Edit', None)  # 填写 通信密码
                PutStr2Edit(NetWork_Serc_hwnd, network_serc)
                time.sleep(0.1)
            confirmBtnHwnd = win32gui.FindWindowEx(LoginWinHwnd, 0, 'Button', u'确定(&Y)')
            if confirmBtnHwnd > 0:
                Clickbtn(confirmBtnHwnd)
            else:
                print(u'未找到 确认按钮，请排查')
        for i in range(10):  # 确认是否登陆成功
            LoginWinHwndNew = win32gui.FindWindow(None, u'用户登录')
            if LoginWinHwndNew > 0 and LoginWinHwndNew == LoginWinHwnd:
                print(u"%s秒后发现登陆窗口还在" % (str(i + 1)))
                time.sleep(1)
                if i == 9:
                    win32gui.SendMessage(LoginWinHwndNew, win32con.WM_SYSCOMMAND, win32con.SC_CLOSE, 0)
                    wx.CallAfter(frame.updateUI, updateLog=u"7s超时登陆失败")
                    return False
            else:
                break
        print(u"登陆购买界面")
        global findFlag_Dialg
        findFlag_Dialg = False
        windows = []
        for i in range(7):  # 关闭营业部公告
            if findFlag_Dialg:
                findFlag_Dialg = False
                break
            win32gui.EnumWindows(Callback_InfoDialog, (windows))
            time.sleep(1)
        print(u"登录完毕")
        wx.CallAfter(frame.updateUI, updateLog=u"登录完毕")

    def ATBuy(self,code,price,num):
        #(stock,buyflag,price,num,money,time,buyresult)
        try:
            global StopATbuy
            if StopATbuy==True:
                    return
            global MAX_BUY_STOCKS
            buy_today_stocks = pickledata(PATH_BUY_STOCK_TODAY)
            if len(buy_today_stocks)>MAX_BUY_STOCKS:
                print(u"进入买股已经达到上限:%i"%(MAX_BUY_STOCKS))
                return
            for item in buy_today_stocks:
                if code  == item[0]:
                    print(u"该股%s已经买入"%(str(code)))
                    return

            global Hwnd_Buy_Btn, Hwnd_BuyNum_Eidt, Hwnd_StockCode_Eidt, Hwnd_BuyEidt_Dlg, Hwnd_BuyPrice_Eidt
            if Hwnd_BuyEidt_Dlg>0:
                PutStr2Edit(Hwnd_StockCode_Eidt, code)
                time.sleep(1)
                PutStr2Edit(Hwnd_BuyPrice_Eidt, price)
                time.sleep(0.5)
                PutStr2Edit(Hwnd_BuyNum_Eidt, num)
                time.sleep(0.5)
                win32gui.SetForegroundWindow(Hwnd_Buy_Btn)
                time.sleep(0.05)
                win32gui.PostMessage(Hwnd_Buy_Btn, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)
                time.sleep(0.001)
                win32gui.PostMessage(Hwnd_Buy_Btn, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, 0)
                time.sleep(0.5)
                GetBuyConfmBtn()# 点击委托确认
            buyresult = GetBuyResultDlg()
            #(stock, buyflag, price, num,  money,time, buyresult)
            buy_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

            money = round(float(price)*int(num),2)
            data = (code,'buy',price,num,money,buy_time,buyresult)
            bylist = pickledata(PATH_BUY_STOCK_TODAY)
            bylist.append(data)
            dumpdata(PATH_BUY_STOCK_TODAY,bylist)
        except Exception as e:
            print(e)
            WrieTxtLogFile('buy att:'+ e)









##########################################################################################################################
    """预警条件：
    1 askbid>askvol 1.2倍
    2 当前价比上一分钟上涨
    3 当前价*1。002〉最高价。
    4 当前量比〉4
    5 涨幅小于1.04
    6 昨日没有涨停
    """




    def FILTER(self):
        wx.CallAfter(frame.updateUI, updateLog=u"后台读取数据库开始")
        DEBUG = False
        global THREAD_RUNNING

        while THREAD_RUNNING:
            print(' begin to read database')
            #path = os.path.split(os.path.realpath(__file__))[0]+os.sep +'bigdata'+os.sep+ '20161028hq.db'  #-===========================
            global G_SELECT_STOCK_RCD_LOG
            G_SELECT_STOCK_RCD_LOG = ''
            sysmbol = self.getselfStockList()
            if sysmbol != []:
                print("symbol len:", len(sysmbol))
                step = 64
                symbol_list_slice = [sysmbol[i: i + step]
                                     for i in range(0, len(sysmbol), step)]
                j = 0
                for symbol_group in symbol_list_slice:
                    try:
                        conn = get_conn(PATH_DATABASE + str(j) + '.db')
                    except Exception as e:
                        j = j + 1
                        print(e)
                        continue
                    for stock in symbol_group:
                        try:
                            data = fetch_data_from_stock_table(conn, stock)
                        except:
                            continue
                        if data == []:
                            #print("data is []")
                            continue
                        res = tuple()
                        try:
                            res = self.askall_minuteVol(stock,data)
                        except Exception as e:
                            print(e)


                        try:
                            self.ConditionSelection(stock,data,PATH_DATABASE + str(j) + '.db',res)
                        except Exception as e:
                           print(e)
                    j = j + 1
            """try:
                WrieTxtLogFile(G_SELECT_STOCK_RCD_LOG)
            except Exception as e:
                print(e)
            global MAX_BUY_THREAD
            MAX_BUY_THREAD = MAX_BUY_THREAD + 1
            if MAX_BUY_THREAD < 10:
                threading._start_new_thread(self.ATBuy,('601288','3.23','100'))"""
            time.sleep(8)

    def askall_minuteVol(self,stock,data):

        global G_MINUTE_RCD_TUPLE

        if G_MINUTE_RCD_TUPLE is None:
            G_MINUTE_RCD_TUPLE = pickledata(PATH_ONE_MINUTE)

        try:
            # onemin_rcd 内容为List,list 中每个tuple 存储一个股票信息，包含一分钟量，委比1.2 委比1.5 ，res为当前stock数据
            res = tuple()
            # [(stock , name , [one_min_time1,one_min_time2] ,[ask1.2_time1,ask1.2_time2],[ask1.5_time1,ask1.5_time2],[ask20_time1,ask20_time2]),()]
            datalene = len(data)
            last_line = data[datalene - 1]
            curr_tm = last_line[1]
            current_min = -1
            current_hour = -1
            current_second = -1
            if type(curr_tm) == str:
                curr_tm = datetime.datetime.strptime(curr_tm, "%Y-%m-%d %H:%M:%S")
                current_min = curr_tm.minute
                current_hour = curr_tm.hour
                current_second = curr_tm.second
            onemin_rcd = G_MINUTE_RCD_TUPLE

            if onemin_rcd is None:
                onemin_rcd = []
            flg_same_one_minu = False
            flg_same_ask12 = False
            flg_same_ask15 = False
            flg_same_ask20 = False
            if onemin_rcd !=[]:
                for item in onemin_rcd:
                    if item[0]==stock:
                        #if current_second > 12:
                            #res = item
                            #return res
                        timelist_one_m = item[2]
                        len_timelist_one_m = len(timelist_one_m)
                        timelist_ask12 = item[3]
                        len_timelist_ask12 = len(timelist_ask12)
                        timelist_ask15 = item[4]
                        len_timelist_ask15 = len(timelist_ask15)
                        timelist_ask20 = item[5]
                        len_timelist_ask20 = len(timelist_ask20)


                        if len_timelist_one_m>0:
                            lasttime_one_m = timelist_one_m[len_timelist_one_m -1]
                            if type(lasttime_one_m) == str:
                                lasttime_one_m = datetime.datetime.strptime(lasttime_one_m, "%Y-%m-%d %H:%M:%S")
                            if current_hour == lasttime_one_m.hour and current_min == lasttime_one_m.minute:
                                flg_same_one_minu = True
                        if len_timelist_ask12 > 0:
                            lasttime_ask12 = timelist_ask12[len_timelist_ask12 - 1]
                            if type(lasttime_ask12) == str:
                                lasttime_ask12 = datetime.datetime.strptime(lasttime_ask12, "%Y-%m-%d %H:%M:%S")
                            if current_hour == lasttime_ask12.hour and current_min == lasttime_ask12.minute:
                                flg_same_ask12 = True
                        if len_timelist_ask15 > 0:
                            lasttime_ask15 = timelist_ask15[len_timelist_ask15 - 1]
                            if type(lasttime_ask15) == str:
                                lasttime_ask15 = datetime.datetime.strptime(lasttime_ask15, "%Y-%m-%d %H:%M:%S")
                            if current_hour == lasttime_ask15.hour and current_min == lasttime_ask15.minute:
                                flg_same_ask15 = True
                        if len_timelist_ask20 > 0:
                            lasttime_ask20 = timelist_ask20[len_timelist_ask20 - 1]
                            if type(lasttime_ask20) == str:
                                lasttime_ask20 = datetime.datetime.strptime(lasttime_ask20, "%Y-%m-%d %H:%M:%S")
                            if current_hour == lasttime_ask20.hour and current_min == lasttime_ask20.minute:
                                flg_same_ask20 = True
                        if len_timelist_one_m >0 or len_timelist_ask12 >0 or len_timelist_ask15 >0 or len_timelist_ask20 >0:
                            res = item
                        if flg_same_one_minu == True and flg_same_ask12 == True and flg_same_ask15 == True and flg_same_ask20 == True:
                            return res
                        else:
                            break

            current_ask_amount = last_line[11]  # 预警条件1 委托总买量 大于 委托总卖量
            current_bid_amount = last_line[12]
            ask12_flg = False
            ask15_flg = False
            ask20_flg = False
            vol_onemin_flg = False

            one_min_index = 0
            if last_line[7] == 'PZ' and datalene > 20 and data[datalene - 20][7] == 'PZ' :
                ##
                if current_bid_amount > 1.2 * current_ask_amount and flg_same_ask12 == False:
                    ask12_flg = True
                if current_bid_amount > 1.5 * current_ask_amount and flg_same_ask15 == False:
                    ask15_flg = True
                if current_bid_amount > 2.0 * current_ask_amount and flg_same_ask20 == False:
                    ask20_flg = True
                ##
                #print("current_hour", current_hour)
                #print("current_min", current_min)
                for i in range(1,datalene):
                    line = data[datalene - i]
                    now_time = line[1]
                    if type(now_time) == str:
                        now_time = datetime.datetime.strptime(now_time, "%Y-%m-%d %H:%M:%S")
                    if current_hour>0 and current_min == 0: # 整点时刻
                        if current_hour - now_time.hour == 1 and now_time.minute == 59:# and now_time.second<60: # 上一分钟前10s
                                one_min_index = i
                        #if (one_min_index>0 and now_time.minute!=59) or (one_min_index==0 and now_time.minute<59):
                        if now_time.minute != current_min and now_time.minute!=59:
                            break
                    if current_hour>0 and current_min>0 :
                        if current_hour == now_time.hour and now_time.minute == current_min-1: #and now_time.second<60: # 上一分钟前10s
                                one_min_index = i
                        #if (one_min_index >0 and now_time.minute != current_min-1) or (one_min_index==0 and now_time.minute<current_min -1) or(now_time.hour<current_hour and  now_time.minute>current_min -1):# BUG
                        if now_time.minute!=current_min and now_time.minute != current_min-1:
                            break

                if one_min_index> 0:

                    now_line = data[datalene - one_min_index]
                    now_line_time = now_line[1]
                    if type(now_line_time) == str:
                        now_line_time = datetime.datetime.strptime(now_line_time, "%Y-%m-%d %H:%M:%S")
                    now_line_second = now_line_time.second
                    totalsecond = (60- now_line_second) + current_second

                    vol_onemin = 0
                    if totalsecond >= 60:
                        one_min_vol = now_line[9]
                        vol_onemin = (last_line[9]-one_min_vol)*60/totalsecond

                    if vol_onemin * 2.2 >  int(last_line[11]) and flg_same_one_minu == False: # 11 current_ask_amount

                        vol_onemin_flg =True

            if vol_onemin_flg == True or ask12_flg == True or ask15_flg == True or ask20_flg == True:
                isexistflg = 0
                if len(onemin_rcd) > 0:
                    for j in range(len(onemin_rcd)):
                        if onemin_rcd[j][0] == stock:
                            isexistflg = 1
                            if vol_onemin_flg == True:
                                onemin_rcd[j][2].append(last_line[1])
                            if ask12_flg ==True:
                                onemin_rcd[j][3].append(last_line[1])
                            if ask15_flg ==True:
                                onemin_rcd[j][4].append(last_line[1])
                            if ask20_flg == True:
                                onemin_rcd[j][5].append(last_line[1])
                            res = onemin_rcd[j]
                            break
                if isexistflg == 0:
                    res = (stock, last_line[0], [],[],[],[])
                    if vol_onemin_flg == True:

                        res[2].append(last_line[1])
                    if ask12_flg == True:
                        res[3].append(last_line[1])
                    if ask15_flg == True:
                        res[4].append(last_line[1])
                    if ask20_flg == True:
                        res[5].append(last_line[1])
                    onemin_rcd.append(res)
                G_MINUTE_RCD_TUPLE = onemin_rcd
                if current_min % 5 == 0:# 5分钟存档一次
                    dumpdata(PATH_ONE_MINUTE, G_MINUTE_RCD_TUPLE)


        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno,e)

        return res






    def ConditionSelection(self,stock,data,dbname,stock_other_info):
        global G_SELECT_STOCK_RCD_LOG
        num_onemin = 0
        num_ask12 = 0
        num_ask15 = 0
        num_ask20 = 0
        try:
            if len(stock_other_info)>0:
                num_onemin = len(stock_other_info[2])
                num_ask12  = len(stock_other_info[3])
                num_ask15 = len(stock_other_info[4])
                num_ask20 = len(stock_other_info[5])
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno, e)

        last_line = data[len(data) - 1]
        if last_line[7] == 'PZ' and len(data)>20 and data[len(data) - 20][7] =='PZ':

            current_ask_amount = last_line[11]  # 预警条件1 委托总买量 大于 委托总卖量
            current_bid_amount = last_line[12]
            ask_money = round(current_ask_amount * last_line[6]/10000,2)
            if not current_bid_amount > ASK_ALL_BID_ALL_RATE  * current_ask_amount:
                return

            G_SELECT_STOCK_RCD_LOG = G_SELECT_STOCK_RCD_LOG +  'stock:' + stock + 'time:'+ last_line[1] + "--->askall" + "\n"

            high = last_line[4]                 # 预警条件3 当前价*1.002〉最高价
            now = last_line[6]
            if not now * NOW_HIGH_RATE > high:
                return

            G_SELECT_STOCK_RCD_LOG = G_SELECT_STOCK_RCD_LOG + 'stock:' + stock + 'time:' + last_line[1] + "--->now high" + "\n"

            last_close = last_line[2]
            zf = STOCK_ZF(last_close, now)      # 预警条件5 涨幅小于4
            if not zf < ZF_MX:
                return

            G_SELECT_STOCK_RCD_LOG = G_SELECT_STOCK_RCD_LOG + 'stock:' + stock + 'time:' + last_line[1] + "--->zf mx" + "\n"

            now_time = last_line[1]
            if type(now_time) == str:
                now_time = datetime.datetime.strptime(now_time, "%Y-%m-%d %H:%M:%S")
            curlb = 0
            if os.path.exists(PATH_SELF_STOCK_NAME):    # 预警条件4  当前量比〉4
                try:
                    hisdata = pd.read_csv(PATH_STOCK_HIS_DATA + os.sep + stock[2:] + '.csv', encoding='gbk')
                    rows = hisdata.shape[0]
                    # print("rows:",rows)
                    v_ma5 = hisdata.iat[rows - 1, 7]
                    # p_change = STOCK_ZF(hisdata.iat[rows - 2, 3], hisdata.iat[rows - 1, 3])  # 昨日涨幅小数点
                    vol = last_line[9]
                    # print("v_ma5:",v_ma5)基础上
                    # print("p_change:", p_change)
                    # if p_change < 9.98:  # 预警条件6  昨日没有涨停
                    # if not ((stock, last_line[0]) in SELECT_LIST_5):
                    curlb = current_lb(vol, v_ma5, now_time)
                except Exception as e:
                    print(e)
                print("curlb:", curlb)
                if curlb >= LB_MX_BEFORE_10 or (now_time.hour >= 10  and curlb >= LB_MX_AFTER_10 ) :
                    G_SELECT_STOCK_RCD_LOG = G_SELECT_STOCK_RCD_LOG + 'stock:' + stock + 'time:' + last_line[1] + "--->curlb mx" + "\n"
                    pkl_file = open(PATH_SELETC_LIST, 'rb')
                    SELECT_LIST = pickle.load(pkl_file)
                    pkl_file.close()
                    mytimelist = stock_other_info[2]
                    len_mytimelist = len(mytimelist)
                    if len_mytimelist<1:
                        return
                    one_min_last_time = mytimelist[len_mytimelist -1]
                    print('one_min_last_time:',one_min_last_time)
                    if type(one_min_last_time)== str:
                        one_min_last_time = datetime.datetime.strptime(one_min_last_time, "%Y-%m-%d %H:%M:%S")
                    if one_min_last_time.minute == now_time.minute:
                        G_SELECT_STOCK_RCD_LOG = G_SELECT_STOCK_RCD_LOG + 'stock:' + stock + 'time:' + last_line[1] + "|||===|||" + "\n"
                        if SELECT_LIST is None:
                            SELECT_LIST = []
                        if not ((stock, last_line[0]) in [(itm[0], itm[1]) for itm in SELECT_LIST]):
                            SELECT_LIST.append((stock, last_line[0],last_line[1],now,round(current_bid_amount/current_ask_amount,2),zf,curlb,0,0,dbname,num_onemin,num_ask12,num_ask15,num_ask20,ask_money))
                            output = open(PATH_SELETC_LIST, 'wb')
                            pickle.dump(SELECT_LIST, output)
                            output.close()




                #股票代码，股票名称，入选时间，入选价格，入选总委比，入选涨幅，入选量比 ，当前价格，买入涨幅,数据库名，入选委买分钟量比


def pickledata(path):
    res = None
    try:
        pkl_file = open(path, 'rb')
        res = pickle.load(pkl_file)
        pkl_file.close()
    except Exception as e:
        print(e)
    return  res

def dumpdata(path,data):
    output = open(path, 'wb')
    pickle.dump(data, output)
    output.close()

def WrieTxtLogFile(log_content):
    try:
        output = open(PATH_LOG_FILE, 'a')
        output.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"-->"+log_content + '\n')
        output.close()
    except Exception as e:
        print(e)


def STOCK_ZF(last_close,now):
    zf = 100*(now - last_close)/last_close
    return round(zf,2)


def getdayStr(delta):
    today=datetime.date.today()
    if delta == 0 :
        return today.strftime('%Y-%m-%d')
    oneday=datetime.timedelta(days=delta)
    yesterday=today-oneday
    return yesterday.strftime('%Y-%m-%d')

def current_lb(vol,v_ma5,now_time):
    #print("vol:",vol)
    #print("v_ma5:", v_ma5)
    h ,m = now_time.hour,now_time.minute
    #print("h:",h)
    #print("m:", m)
    hh,mm=0,0
    if h>11 and m>30:
        hh = 2+ h-13
        mm= m
    else:
       hh = h-9
       mm = m - 30

    lb = vol*240/(hh*60+mm)/v_ma5
    return round(lb,2)


###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

def PutStr2Edit(hwnd,Inputstr):#输入字符到Edit控件中
    win32gui.SendMessage(hwnd, win32con.WM_SETTEXT,None, '')#有字符且致则清空
    res=win32api.SendMessage(hwnd, win32con.WM_SETTEXT, None,Inputstr)


def Clickbtn(btnhld):
    win32gui.PostMessage(btnhld, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)

    win32gui.PostMessage(btnhld, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, 0)

    win32gui.PostMessage(btnhld, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)

    win32gui.PostMessage(btnhld, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, 0)

def Callback_InfoDialog(hwnd, extra):
    if win32gui.GetClassName(hwnd)=="#32770":
        if win32gui.FindWindowEx(hwnd, 0, 'Static', u'营业部公告')>0:
            ConfirmbtnHwnd=win32gui.FindWindowEx(hwnd, 0, 'Button', u'确定')
            if ConfirmbtnHwnd>0:
                global findFlag_Dialg
                findFlag_Dialg = True
                Clickbtn(ConfirmbtnHwnd)
                #win32gui.PostMessage(ConfirmbtnHwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)
                #win32gui.PostMessage(ConfirmbtnHwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, 0)
            else:
                print (u"营业部公告 确定按钮查找失败!!")



def Callback_MainWind(hwnd, extra):
    if win32gui.GetWindowText(hwnd) == title_ht:
        global MainWinList
        if not (hwnd in MainWinList):
            MainWinList.append(hwnd)

def findStockzijinHwnd(hwnd,ht_Account):#查找资金帐号
    #print "findStockzijinHwnd hwnd:",hwnd
    res = False
    ToolbarWindow32=win32gui.FindWindowEx(hwnd, 0, 'ToolbarWindow32', None)
    if not ToolbarWindow32>0:
        return res
    phandle=win32gui.FindWindowEx(ToolbarWindow32, 0, '#32770', None)
    handle=win32gui.FindWindowEx(phandle, 0, 'ComboBox', None)
    for i in range(3):
        buff_len = win32gui.SendMessage(handle, win32con.CB_GETLBTEXTLEN, 0)
        #print("buff_len:",buff_len)
        buffer = '0' * (buff_len+1)
        buffer1 = '0' * (buff_len + 1)
        win32gui.SendMessage(handle,win32con.CB_GETLBTEXT,0,buffer)

        #print "ht_Account:",ht_Account[-4:]
        #print "buffer:",buffer.decode("gbk")
        #print "handle:",handle


        if ht_Account[-4:] in buffer:
            res =True
            break
        else:
            buff_len = win32gui.SendMessage(handle, win32con.CB_GETLBTEXTLEN, 0)
            buffer = '0' * (buff_len+1)
            handle=win32gui.FindWindowEx(phandle, handle, 'ComboBox', None)
    return res


def getTreeHwnd(hwnd):
    win_AfxMDIFrame42s = win32gui.FindWindowEx(hwnd, 0, 'AfxMDIFrame42s', None)
    # print "win_AfxMDIFrame42s:%x"%(win_AfxMDIFrame42s)
    win_AfxWnd42s = win32gui.FindWindowEx(win_AfxMDIFrame42s, 0, 'AfxWnd42s', None)
    # print "win_AfxWnd42s:%x"%(win_AfxWnd42s)
    win_Afx = win32gui.FindWindowEx(win_AfxWnd42s, 0, 'Afx:400000:0', None)
    # print "win_Afx:%x"%(win_Afx)
    win_AfxWnd42s = win32gui.FindWindowEx(win_Afx, 0, 'AfxWnd42s', None)
    # print "win_AfxWnd42s:%x"%(win_AfxWnd42s)
    win_SysTreeView32 = win32gui.FindWindowEx(win_AfxWnd42s, 0, 'SysTreeView32', None)
    # print "win_SysTreeView32:%x"%(win_SysTreeView32)
    if win_SysTreeView32 > 0:
        print(u"查找树形子窗口句柄%x" % (win_SysTreeView32))
        return win_SysTreeView32
    else:
        print(u"查找树形子窗口句柄异常，请排除代码")
        return False

def ClickBuyFrmTree(Treehwnd):
    if not Treehwnd:
        print(u"树形控件句柄为None，请排除代码")
        return False
    FirstItemHandle = SendMessage(Treehwnd, TVM_GETNEXTITEM ,TVGN_FIRSTVISIBLE,None);
    if FirstItemHandle:
        SendMessage(Treehwnd, TVM_SELECTITEM,TVGN_CARET,FirstItemHandle);
    return True

def GetBuyEidtHwnd(MainWinHdwn,Treehwnd):
    if Treehwnd > 0:
        ClickBuyFrmTree(Treehwnd)
        time.sleep(0.2)
    global Hwnd_Buy_Btn,Hwnd_BuyNum_Eidt,Hwnd_StockCode_Eidt,Hwnd_BuyEidt_Dlg,Hwnd_BuyPrice_Eidt
    Hwnd_Buy_Btn=0
    Hwnd_BuyNum_Eidt=0
    Hwnd_StockCode_Eidt=0
    Hwnd_BuyEidt_Dlg=0
    Hwnd_BuyPrice_Eidt=0
    parent=win32gui.FindWindowEx(MainWinHdwn, 0, 'AfxMDIFrame42s', None)
    index=5
    while index > 0:
        if index==5:
            Dlg=win32gui.FindWindowEx(parent,0, '#32770', None)
        else:
            Dlg=win32gui.FindWindowEx(parent,Dlg, '#32770', None)
        Hwnd_Buy_Btn=win32gui.FindWindowEx(Dlg,0, 'Button', u'买入[B]')
        if Hwnd_Buy_Btn>0:
            Hwnd_BuyEidt_Dlg=Dlg
            break;
        index -= 1
    if Hwnd_BuyEidt_Dlg>0:
        #print (u"找到填写买入股票Eidt的对话框",Hwnd_BuyEidt_Dlg)
        Hwnd_StockCode_Eidt=win32gui.FindWindowEx(Hwnd_BuyEidt_Dlg,0, 'Edit', None)
        #print "Hwnd_StockCode_Eidt",Hwnd_StockCode_Eidt
        Hwnd_BuyPrice_Eidt=win32gui.FindWindowEx(Hwnd_BuyEidt_Dlg,Hwnd_StockCode_Eidt, 'Edit', None)
        #print "Hwnd_BuyPrice_Eidt",Hwnd_BuyPrice_Eidt
        Hwnd_BuyNum_Eidt=win32gui.FindWindowEx(Hwnd_BuyEidt_Dlg,Hwnd_BuyPrice_Eidt, 'Edit', None)
        #print "Hwnd_BuyNum_Eidt",Hwnd_BuyNum_Eidt
        print( 'Hwnd_StockCode_Eidt:',hex(Hwnd_StockCode_Eidt),'\nHwnd_BuyPrice_Eidt:',hex(Hwnd_BuyPrice_Eidt),'\nHwnd_BuyNum_Eidt:',hex(Hwnd_BuyNum_Eidt),'\nHwnd_Buy_Btn:',hex(Hwnd_Buy_Btn ))
        return True

    else:
        print(u"未发现 买入股票Eidt")
        return False

def GetBuyConfmBtn():#获取委托确认 是(&Y)按钮
    windows = []
    hwnd_BuyConfm_dialog=0
    hwnd_BuyConfm_btn = 0
    for i in range(3):
        win32gui.EnumWindows(_P_Callback_BuyConfmBtn, (windows))
        if hwnd_BuyConfm_dialog>0:
            hwnd_BuyConfm_btn=win32gui.FindWindowEx(hwnd_BuyConfm_dialog, 0, u'Button', '是(&Y)'.encode('gbk'))
            if hwnd_BuyConfm_btn>0:
                Clickbtn(hwnd_BuyConfm_btn)
                print(u" 找到委托确认 是(&Y)按钮:", hwnd_BuyConfm_btn)
                break
            else:
                print (u" 找到委托确认窗口,没有找到委托确认-是Y-按钮子控件")
        else:
            print (u" 没有找到委托确认窗口")


def _P_Callback_BuyConfmBtn( hwnd, extra ):#获取返回时间父亲窗口回调
    if win32gui.GetClassName(hwnd)=="#32770":
        if win32gui.FindWindowEx(hwnd, 0, u'Static', u'委托确认')>0:
            global hwnd_BuyConfm_dialog
            hwnd_BuyConfm_dialog=hwnd
            #print u" 找到委托确认窗口:",hwnd_BuyConfm_dialog

def GetBuyResultDlg():#获取买入成功对话框内容
    windows = []
    results=[]
    m_index = []
    global hwnd_current_time_dialog
    global str_current_time
    hwnd_current_time_dialog=0# 初始赋值
    str_dlg_info_content=''
    for i in range(3):
        win32gui.EnumWindows(_P_Callback_TimeDialog, (windows))
        if hwnd_current_time_dialog>0:
            #win32gui.EnumChildWindows(hwnd_current_time_dialog, _C_CallBack_TimeDialog, (results, m_index))
            str_dig_info_Hwnd = win32gui.FindWindowEx(hwnd_current_time_dialog, 0, u'Static', None)
            buffer = '0' *200
            len = win32gui.SendMessage(str_dig_info_Hwnd, win32con.WM_GETTEXTLENGTH)+1 #获取edit控件文本长度
            win32gui.SendMessage(str_dig_info_Hwnd, win32con.WM_GETTEXT, len, buffer) #读取文本
            str_dlg_info_content = buffer
            #if u"提交失败" in str_dlg_info_content:
            print(str_dlg_info_content)

            ConfirmBtn=0
            ConfirmBtn=win32gui.FindWindowEx(hwnd_current_time_dialog, 0, 'Button', u'确定')
            if ConfirmBtn>0:
                print (u" 找到确定按钮")
                Clickbtn(ConfirmBtn)
                time.sleep(0.5)
            else:
                print (u"没有找到确定按钮")
            break
        else:
            time.sleep(0.4)
    return str_dlg_info_content

def _P_Callback_TimeDialog( hwnd, extra ):#获取返回时间父亲窗口回调
    if win32gui.GetClassName(hwnd)=="#32770":
        flag1= win32gui.FindWindowEx(hwnd, 0, u'Button', u'确定')
        flag2=win32gui.FindWindowEx(hwnd, 0, u'Static', u'提示')
        if flag1>0 and flag2>0:
            global hwnd_current_time_dialog
            hwnd_current_time_dialog=hwnd
            #print u" 找到提交失败窗口"
def a22():
    print()
###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

###########################################################################################################################

def CreatSomeFile():
    if not os.path.exists(__GPATH__+ os.sep +DATA):
        os.makedirs(__GPATH__+ os.sep +DATA)
    if not os.path.exists(PATH_SELETC_LIST):
        output = open(PATH_SELETC_LIST, 'wb')
        SELECT_LIST = []
        pickle.dump(SELECT_LIST, output)
        output.close()
    if not os.path.exists(PATH_ONE_MINUTE):
        output = open(PATH_ONE_MINUTE, 'wb')
        ONEMINI_LIST = []
        pickle.dump(ONEMINI_LIST, output)
        output.close()
    if not os.path.exists(PATH_BUY_STOCK_TODAY):
        output = open(PATH_BUY_STOCK_TODAY, 'wb')
        BUY_TODAY_LIST = []
        pickle.dump(BUY_TODAY_LIST, output)
        output.close()
    if not os.path.exists(PATH_BUY_SELECT_STOCK):
        output = open(PATH_BUY_SELECT_STOCK, 'wb')
        BUY_select_LIST = []
        pickle.dump(BUY_select_LIST, output)
        output.close()
    if not os.path.exists(PATH_LOG_FILE):
        output = open(PATH_LOG_FILE, 'wb')
        output.close()


if __name__ == '__main__':
    CreatSomeFile()
    global frame
    app = wx.App()
    frame =MyFrame2(None)
    frame.Show()
    app.MainLoop()





    # 0 name
    # 1 time
    # 2 last_close 昨日收盘价
    #3 open
    #4 high
    #5 low
    #6 now
    #7 status
    #8 transaction_count
    #9 total_volume 总手
    #10 total_amount 总额
    # 11 current_ask_amount 所有委托卖量
    # 12 current_bid_amount 所有委托买量



"""
流通市值:=C*CAPITAL*VOLUNIT/100000000;
L1:=流通市值<60;
L2:=(close-ref(close,20))/ref(close,20)*100<20;
L3:=count(c/ref(c,1)>1.099,200)>2;
L4:=c/ref(c,1)<1.099;
OUT: L1 AND L2 AND L3 AND L4;
"""




