from mitmproxy.net.http.http1.assemble import assemble_request, assemble_response
from mitmproxy import ctx

class ReadResponse:

	def __init__(self):
		self.num =0

	def response(self,flow):
		self.num = self.num +1
		ctx.log.info("We've seen %d responses" % self.num)
		with open('/home/pptruser/app/PhishMeshCrawler/output.txt', 'a') as f:
			f.write("=== REQUEST ======>>>\n")
			f.write(assemble_request(flow.request).decode('utf-8'))
			if flow.response:
				f.write("<<<===== RESPONSE ===\n")
				f.write(assemble_request(flow.response).decode('utf-8'))

	def request(self,flow):
		self.num = self.num +1
		ctx.log.info("We've seen %d requests" % self.num)


addons = [ReadResponse()]
        
