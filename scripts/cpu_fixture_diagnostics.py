"""僅驗收固定公開health影像時擷取有界stderr；產品WorkerRunner仍只排空、不保存文件診斷。"""
class FixtureStderr:
    def __init__(self, source, destination, limit=4096):
        self.source=source;self.destination=destination;self.limit=limit;self.kept=0
        with destination.open('xb'):pass

    def read(self, size=-1):
        data=self.source.read(size)
        keep=data[:max(0,self.limit-self.kept)]
        if keep:
            with self.destination.open('ab') as output:output.write(keep)
            self.kept+=len(keep)
        return data

    def __getattr__(self, name):
        return getattr(self.source,name)
