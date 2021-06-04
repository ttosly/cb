# -*- coding : cp939 -*-
import urllib.request,time,datetime,json,sys
import socket,socks,csv

from dingtalkchatbot.chatbot import DingtalkChatbot

class bound(object):
    def __init__(self,csvf):
        #init database
        self.sd=[]
        f=csv.reader(open(csvf,'r'))
        for line in f :
            self.sd.append(line)
        #print(self.sd)
        
        self.datas=[]
    def get_html(self,url):
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1080)
        socket.socket = socks.socksocket
        value = urllib.request.urlopen(url).read()
        return value
    def proc_jsl(self):
        url_tmp='https://www.jisilu.cn/data/cbnew/cb_list/?___t=%s'
        #li=[]
        url = url_tmp % int(time.time())
        #print(url)

        value = self.get_html(url)
        dic = json.loads(value)
        
        for row in dic['rows']:
            mc=row['cell']['bond_nm']
            cjl =float(row['cell']['volume'])
            sj= float(row['cell']['price'])
            if ('EB' in mc) or ((cjl==0) and (sj==100)):  #filter out EB and Fresh
                continue
            else:
                code=row['id']
                mc=row['cell']['bond_nm']
                stock_nm=row['cell']['stock_nm']
                gj= float(row['cell']['sprice'])
                zgj= float(row['cell']['convert_price'])
                pj=row['cell']['rating_cd']
                try:
                  sqsy=float(row['cell']['ytm_rt'].strip('%')) 
                  shsy=float(row['cell']['ytm_rt_tax'].strip('%'))
                except:
                  sqsy=0.0  
                  shsy=0.0   
                volume=float(row['cell']['volume'])
                sygm=float(row['cell']['curr_iss_amt'])
                stock_id=row['cell']['stock_id']
                fxgm = float(row['cell']['orig_iss_amt'])
                bound_id =row['cell']['pre_bond_id']
                self.datas.append([code,mc,stock_nm,sj,gj ,time.strftime("%Y-%m-%d",time.localtime()),zgj,pj,sqsy,shsy,volume,sygm,stock_id,fxgm])
        
    def proc_gtimg(self):
        
        datas=[]
        
        for data in self.datas:
          #print len(self.datas)
          
          s_id=data[-2]# stock code
          b_id=s_id[:2]+data[0] #bound code sh601988[0:2]=sh
          url = 'http://qt.gtimg.cn/q='+b_id+','+s_id          

          value=self.get_html(url)
          value= value.decode("gbk").split(';')
          b_str=value[0]
          s_str=value[1]
         # print (url,b_str,"###",s_str)
          cjl=float(b_str.split('=')[1].split('~')[36])*10
          sid=s_str.split('=')[0].strip('v_')         
          ltsz=float(s_str.split('=')[1].split('~')[44])
          zsz=float(s_str.split('=')[1].split('~')[45])
          hsl=round((cjl/(data[-3]*1000000)*100),2) #剩余规模*1百万等于剩余张数 结果*100 转化为百分比
          
          datas.append(data+[cjl,hsl,zsz,ltsz])
          
        self.datas=datas
    def proc_gtimg_1(self):
        datas=[]
        
        url = 'http://qt.gtimg.cn/q='
        contents=""
        max_id= len(self.datas)-1
        i=1

        for data in self.datas:
          #print len(self.datas)
          
          s_id=data[-2]# stock code
          b_id=s_id[:2]+data[0] #bound code sh601988[0:2]=sh
          url = url+(b_id+','+s_id+",")
          #if (i % 30 ==0 )or(data==self.datas[max_id]):
          if (i % 30 ==0 )or(i==max_id+1):
             
             value=self.get_html(url)
             
             contents=contents +value.decode("gbk")
             i=i+1
             url='http://qt.gtimg.cn/q='
          else:
             i=i+1
        #print("Get down")
        
        value=contents.split(';')
        j=0
        while j  < len(value)-1:
          b_str=value[j]
          s_str=value[j+1]
          cjl=float(b_str.split('=')[1].split('~')[36])*10
          sid=s_str.split('=')[0].strip('v_')         
          ltsz=float(s_str.split('=')[1].split('~')[44])
          zsz=float(s_str.split('=')[1].split('~')[45])
          hsl=round((cjl/(self.datas[j//2][-3]*1000000)*100),2) #剩余规模*1百万等于剩余张数 结果*100 转化为百分比
          datas.append(self.datas[j//2]+[cjl,hsl,zsz,ltsz])
               #print (j,datas[-1])
          j=j+2
          
        self.datas=datas
        
    def send_msg(self):
        #'通过钉钉推送信息到手机2021-01-11
        def avg(li,n=2):
            return(round(sum(li)/len(li),n))
        def mid(li):
            li.sort()
            return(li[int(len(li)/2)])
        #'初始化钉钉
        
        #'准备信息
        code=[i[0] for i in self.datas]
        name=[i[1] for i in self.datas]
        xj=[i[3] for i in self.datas] #转债价
        gj=[i[4] for i in self.datas] #正股从
        zgj=[i[6] for i in self.datas] #转股价
        sygm=[i[11] for i in self.datas] #剩余规模
        yj=[nxj/(ngj/nzgj*100)-1 for nxj,ngj,nzgj in zip(xj,gj,zgj)] #溢价
        sd=[nxj+nyj*100 for nxj,nyj in zip(xj,yj)] #双低值
        list_gm_yj=[[scode,sname,nxj,nsd] for scode,sname,nxj,nsd,nsygm,nyj in zip (code,name,xj,sd,sygm,yj) if nsygm<10 and nyj<15] #筛选规模小于10亿，溢价小于15
        list_gm_yj=sorted(list_gm_yj,key=lambda x:x[3]) #按双低值排序
        sxsd=list_gm_yj[:100]#选前25
        sxsdcode=[x[0] for x in sxsd]
        found=[]
        for sd in self.sd:
            for i in range(25):
                #print(sd[0],sxsd[i][0])
                if sd[0]==sxsd[i][0]:
                    
                    found.append(i)
                    break
                elif i==24:
                    print('轮出:'+sd[1]+' ,双低排名'+str(sxsdcode.index(sd[0])))
        print ('可轮入:')
        for i in range(25):
            
            if not i in found:
                print ('双低排名 %d ，%s [%s],价格%.2f,双低值%.2f'%(i,sxsd[i][0],sxsd[i][1],sxsd[i][2],sxsd[i][3]))
                    
        
    def save(self):
        for data in self.datas:
            sql = 'insert into kzz values('+('?,'*len(data))[:-1]+')'
            self.cu.execute (sql,data)
        self.conn.commit()
        self.conn.close()
    def update(self):
        self.proc_jsl()
        print ('Jsl OK')
        self.proc_gtimg_1()
        print ('Gtimg OK')
        self.save()
        print ('Save OK!!!')
        self.send_msg()
    def test(self,out=1):
        self.proc_jsl()
        print ('同步数据完成')
        #self.proc_gtimg_1()
        #print ('Gtimg OK')
        self.send_msg()
        
        
        '''if out==1 :
            for data in self.datas:
                print(data)'''
        
#ver 190727
#ver 210204 加入启动参加方便调试
#ver 210324 加入前20双低均价
if __name__=="__main__":
    
  if datetime.datetime.now().weekday()<5 :
     abound=bound(r'e:/sd.csv')
     abound.test()
     
      
      
