import os

from win32com.client import Dispatch


class d2p(object) :
    def __init__(self):
        self.word = Dispatch('Word.Application')
        
    def __del__(self):
        self.word.Quit()
        
    def doc2pdf(self,path,in_file,outpath="pdf"):
        wdFormatPDF = 17
        doc=self.word.Documents.Open(os.path.join(path,in_file))
        in_file=in_file.replace(".docx", ".pdf")
        in_file=in_file.replace(".doc", ".pdf")
        out_file= os.path.join(path,outpath,in_file)
        #print (out_file)
        doc.SaveAs(out_file, FileFormat=wdFormatPDF)
        doc.Close()
        
if __name__ == "__main__":
    root=os.path.abspath(".")
    
    print ("Word批量转PDF\n\n正在处理目录:%s\n"%root)
    
    if not os.path.exists(os.path.join(root,"pdf")):
        os.mkdir(os.path.join(root,"pdf"))
        
    word=d2p()
    
    for f in os.listdir(root):
        if f.endswith(".doc") or f.endswith(".docx"):
            print (f)
            word.doc2pdf(root,f)
    del word

