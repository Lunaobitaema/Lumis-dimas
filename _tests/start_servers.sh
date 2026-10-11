#!/bin/bash
# Fresh copies of the site for testing: A = relaxed rate limit + notification mocks, B = stock config.
S=/tmp/claude-0/-home-claude/dde88c5a-a2c4-53ed-b1c3-7fd04d8963fa/scratchpad
pkill -f "[p]hp .*-S 127.0.0.1:880[34]" 2>/dev/null; pkill -f "[t]g_mock.py" 2>/dev/null; sleep 0.5
rm -rf $S/siteA $S/siteB $S/mail.log $S/tg.log
cp -r /home/claude/lumis/work $S/siteA; cp -r /home/claude/lumis/work $S/siteB
rm -rf $S/siteA/storage/data-* $S/siteB/storage/data-* $S/siteA/uploads/*.{jpg,png,webp} $S/siteB/uploads/*.{jpg,png,webp} 2>/dev/null
sed -i "s/'lead_rate_max'    => 5,/'lead_rate_max'    => 1000,/; s#'telegram_bot_token' => ''#'telegram_bot_token' => 'TESTTOKEN'#; s#'telegram_chat_id'   => ''#'telegram_chat_id'   => '12345'#; s#'telegram_api_base'  => 'https://api.telegram.org'#'telegram_api_base'  => 'http://127.0.0.1:8805'#" $S/siteA/api/config.php
printf '#!/bin/bash\ncat >> /tmp/claude-0/-home-claude/dde88c5a-a2c4-53ed-b1c3-7fd04d8963fa/scratchpad/mail.log\necho "=====END=====" >> /tmp/claude-0/-home-claude/dde88c5a-a2c4-53ed-b1c3-7fd04d8963fa/scratchpad/mail.log\n' > $S/fake_sendmail.sh; chmod +x $S/fake_sendmail.sh
cat > $S/tg_mock.py <<'PY'
import http.server, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); body=self.rfile.read(n)
        open(sys.argv[1],'ab').write(self.path.encode()+b'\n'+body+b'\n=====END=====\n')
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(b'{"ok":true}')
    def log_message(self,*a): pass
http.server.HTTPServer(('127.0.0.1',8805),H).serve_forever()
PY
(nohup python3 $S/tg_mock.py $S/tg.log >/dev/null 2>&1 &)
for p in 8803:siteA 8804:siteB; do
  (cd $S/${p#*:} && nohup php -d upload_max_filesize=10M -d post_max_size=55M -d max_file_uploads=6 -d sendmail_path=$S/fake_sendmail.sh -S 127.0.0.1:${p%:*} -t . >$S/php${p%:*}.log 2>&1 &)
done
sleep 1.5; curl -s http://127.0.0.1:8803/api/content.php; echo; curl -s http://127.0.0.1:8804/api/content.php; echo
