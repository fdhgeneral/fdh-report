import base64, pathlib

B = (
    "PHNjcmlwdD4KKGZ1bmN0aW9uKCl7CiAgdmFyIHNBPWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJt"
    "Z3ItYSIpOwogIHZhciBzQj1kb2N1bWVudC5nZXRFbGVtZW50QnlJZCgibWdyLWIiKTsKICB2YXIg"
    "cmVzPWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJoMmgtcmVzdWx0Iik7CiAgaWYoIXNBfHwhc0J8"
    "fCFyZXMpcmV0dXJuOwogIHZhciBIPXdpbmRvdy5GREhfSDJIfHx7fTsKICBmdW5jdGlvbiBmKG4p"
    "e3JldHVybihNYXRoLnJvdW5kKE51bWJlcihuKSoxMCkvMTApLnRvRml4ZWQoMSk7fQogIGZ1bmN0"
    "aW9uIGdvKCl7CiAgICB2YXIgYT1zQS52YWx1ZS50cmltKCksYj1zQi52YWx1ZS50cmltKCk7CiAg"
    "ICBpZighYXx8IWIpe3Jlcy5pbm5lckhUTUw9IjxwIGNsYXNzPVwiaDJoLXBsYWNlaG9sZGVyXCI+"
    "U2VsZWN0IHR3byBtYW5hZ2VycyB0byBzZWUgdGhlaXIgcmVjb3JkLjwvcD4iO3JldHVybjt9CiAg"
    "ICBpZihhPT09Yil7cmVzLmlubmVySFRNTD0iPHAgY2xhc3M9XCJoMmgtcGxhY2Vob2xkZXJcIj5T"
    "ZWxlY3QgdHdvIGRpZmZlcmVudCBtYW5hZ2Vycy48L3A+IjtyZXR1cm47fQogICAgdmFyIGs9W2Es"
    "Yl0uc29ydCgpLmpvaW4oInwiKSxkPUhba107CiAgICBpZighZCl7cmVzLmlubmVySFRNTD0iPHAg"
    "Y2xhc3M9XCJoMmgtcGxhY2Vob2xkZXJcIj5ObyBtYXRjaHVwcyBmb3VuZCBiZXR3ZWVuIDxzdHJv"
    "bmc+IithKyI8L3N0cm9uZz4gYW5kIDxzdHJvbmc+IitiKyI8L3N0cm9uZz4uPC9wPiI7cmV0dXJu"
    "O30KICAgIHZhciBmbD0oZC5hIT09YSk7CiAgICB2YXIgd0E9Zmw/ZC53aW5zX2I6ZC53aW5zX2Es"
    "d0I9Zmw/ZC53aW5zX2E6ZC53aW5zX2I7CiAgICB2YXIgcGZBPWZsP2QucGZfYjpkLnBmX2EscGZC"
    "PWZsP2QucGZfYTpkLnBmX2I7CiAgICB2YXIgcGdBPWZsP2QucHBnX2I6ZC5wcGdfYSxwZ0I9Zmw/"
    "ZC5wcGdfYTpkLnBwZ19iOwogICAgdmFyIGNBPXdBPndCPyJ3aW4iOndBPHdCPyJsb3NlIjoidGll"
    "ZCI7CiAgICB2YXIgY0I9d0I+d0E/IndpbiI6d0I8d0E/Imxvc2UiOiJ0aWVkIjsKICAgIHZhciBi"
    "dz1kLmJpZ2dlc3Rfd2lufHx7fSxjbD1kLmNsb3Nlc3RfZ2FtZXx8e30sc2s9ZC5zdHJlYWt8fHt9"
    "OwogICAgdmFyIGJ3Q3R4PShidy5zY29yZV93IT09dW5kZWZpbmVkKT8iKCIrZihidy5zY29yZV93"
    "KSsiXHUyMDEzIitmKGJ3LnNjb3JlX2wpKyIsICIrKGJ3LmNvbnRleHR8fCIiKSsiKSI6IigiKyhi"
    "dy5jb250ZXh0fHwiIikrIikiCiAgICB2YXIgcG89ZC5wbGF5b2ZmX21lZXRpbmdzPjA/IjxkaXYg"
    "Y2xhc3M9XCJoMmgtY2VudGVyLW1ldGFcIj4mIzk4ODk7ICIrZC5wbGF5b2ZmX21lZXRpbmdzKyIg"
    "cGxheW9mZjwvZGl2PiI6IiI7CiAgICB2YXIgc3I9IiI7CiAgICBpZihkLnNlYXNvbnMpe09iamVj"
    "dC5rZXlzKGQuc2Vhc29ucykuc29ydCgpLmZvckVhY2goZnVuY3Rpb24oeXIpewogICAgICB2YXIg"
    "cz1kLnNlYXNvbnNbeXJdOwogICAgICB2YXIgd2E9Zmw/cy53aW5zX2I6cy53aW5zX2Esd2I9Zmw/"
    "cy53aW5zX2E6cy53aW5zX2I7CiAgICAgIHNyKz0iPHRyPjx0ZD4iK3lyKyI8L3RkPjx0ZCBzdHls"
    "ZT1cImZvbnQtd2VpZ2h0OjYwMFwiPiIrd2ErIlx1MjAxMyIrd2IrIjwvdGQ+PHRkPiIrcy5tZWV0"
    "aW5ncysiIGdhbWUiKyhzLm1lZXRpbmdzIT09MT8icyI6IiIpKyI8L3RkPjwvdHI+IjsKICAgIH0p"
    "O30KICAgIHZhciBoPSI8ZGl2IGNsYXNzPVwiaDJoLXJlc3VsdC1jYXJkXCI+IgogICAgICArIjxk"
    "aXYgY2xhc3M9XCJoMmgtcmVzdWx0LWhlYWRlclwiPiIKICAgICAgICArIjxkaXYgY2xhc3M9XCJo"
    "MmgtcmVzdWx0LXNpZGVcIj48ZGl2IGNsYXNzPVwiaDJoLXJlc3VsdC1uYW1lXCI+IithKyI8L2Rp"
    "dj48ZGl2IGNsYXNzPVwiaDJoLXdpbnMgIitjQSsiXCI+Iit3QSsiPC9kaXY+PGRpdiBjbGFzcz1c"
    "ImgyaC1wdHNcIj4iK2YocGZBKSsiIHB0cyAmYnVsbDsgIitwZ0ErIiBQUEc8L2Rpdj48L2Rpdj4i"
    "CiAgICAgICAgKyI8ZGl2IGNsYXNzPVwiaDJoLWNlbnRlclwiPjxkaXYgY2xhc3M9XCJoMmgtY2Vu"
    "dGVyLXZzXCI+VlM8L2Rpdj48ZGl2IGNsYXNzPVwiaDJoLWNlbnRlci1tZXRhXCI+IitkLm1lZXRp"
    "bmdzKyIgbWVldGluZ3M8L2Rpdj4iK3BvKyI8L2Rpdj4iCiAgICAgICAgKyI8ZGl2IGNsYXNzPVwi"
    "aDJoLXJlc3VsdC1zaWRlXCI+PGRpdiBjbGFzcz1cImgyaC1yZXN1bHQtbmFtZVwiPiIrYisiPC9k"
    "aXY+PGRpdiBjbGFzcz1cImgyaC13aW5zICIrY0IrIlwiPiIrd0IrIjwvZGl2PjxkaXYgY2xhc3M9"
    "XCJoMmgtcHRzXCI+IitmKHBmQikrIiBwdHMgJmJ1bGw7ICIrcGdCKyIgUFBHPC9kaXY+PC9kaXY+"
    "IgogICAgICArIjwvZGl2PiIKICAgICAgKyI8ZGl2IGNsYXNzPVwiaDJoLWZhY3RzXCI+IgogICAg"
    "ICAgICsiPGRpdiBjbGFzcz1cImgyaC1mYWN0XCI+JiMxMjc5NDI7IDxiPkJpZ2dlc3Qgd2luOjwv"
    "Yj4gIisoYncud2lubmVyfHwiPyIpKyIgKyIrYncubWFyZ2luKyIgcHRzICIrYndDdHgrIjwvZGl2"
    "PiIKICAgICAgICArIjxkaXYgY2xhc3M9XCJoMmgtZmFjdFwiPiYjMTI4MjkzOyA8Yj5TdHJlYWs6"
    "PC9iPiAiKyhzay5ob2xkZXJ8fCI/IikrIiAmbWRhc2g7ICIrKHNrLmNvdW50fHwxKSsiVyBpbiBh"
    "IHJvdzwvZGl2PiIKICAgICAgICArIjxkaXYgY2xhc3M9XCJoMmgtZmFjdFwiPiYjOTIwMzsgPGI+"
    "Q2xvc2VzdCBnYW1lOjwvYj4gIisoY2wud2lubmVyfHwiPyIpKyIgKyIrKGNsLm1hcmdpbnx8MCkr"
    "IiBwdHMgKCIrKGNsLmNvbnRleHR8fCIiKSsiKS48L2Rpdj4iCiAgICAgICsiPC9kaXY+IgogICAg"
    "ICArIjxkaXYgY2xhc3M9XCJoMmgtYnJlYWtkb3duXCI+PGg0PlNlYXNvbiBCcmVha2Rvd248L2g0"
    "PiIKICAgICAgICArIjx0YWJsZT48dGhlYWQ+PHRyPjx0aD5TZWFzb248L3RoPjx0aD4iK2ErIjwv"
    "dGg+PHRoPkdhbWVzPC90aD48L3RyPjwvdGhlYWQ+PHRib2R5PiIrc3IrIjwvdGJvZHk+PC90YWJs"
    "ZT4iCiAgICAgICsiPC9kaXY+PC9kaXY+IjsKICAgIHJlcy5pbm5lckhUTUw9aDsKICB9CiAgc0Eu"
    "YWRkRXZlbnRMaXN0ZW5lcigiY2hhbmdlIixnbyk7CiAgc0IuYWRkRXZlbnRMaXN0ZW5lcigiY2hh"
    "bmdlIixnbyk7CiAgdHJ5ewogICAgdmFyIGtzPU9iamVjdC5rZXlzKEgpOwogICAgaWYoa3MubGVu"
    "Z3RoKXsKICAgICAgdmFyIHRvcD1rcy5yZWR1Y2UoZnVuY3Rpb24oYixrKXtyZXR1cm4oIWJ8fEhb"
    "a10ubWVldGluZ3M+SFtiXS5tZWV0aW5ncyk/azpiO30sbnVsbCk7CiAgICAgIGlmKHRvcCl7CiAg"
    "ICAgICAgdmFyIG9wcz1bXS5zbGljZS5jYWxsKHNBLm9wdGlvbnMpLm1hcChmdW5jdGlvbihvKXty"
    "ZXR1cm4gby52YWx1ZTt9KTsKICAgICAgICBpZihvcHMuaW5kZXhPZihIW3RvcF0uYSk+LTEpc0Eu"
    "dmFsdWU9SFt0b3BdLmE7CiAgICAgICAgaWYob3BzLmluZGV4T2YoSFt0b3BdLmIpPi0xKXNCLnZh"
    "bHVlPUhbdG9wXS5iOwogICAgICAgIGdvKCk7CiAgICAgIH0KICAgIH0KICB9Y2F0Y2goZSl7Y29u"
    "c29sZS53YXJuKCJGREggSDJIIGF1dG8tbG9hZDoiLGUpO30KfSkoKTsKKGZ1bmN0aW9uKCl7CiAg"
    "dmFyIGlucD1kb2N1bWVudC5nZXRFbGVtZW50QnlJZCgiaDJoLXNlYXJjaCIpOwogIHZhciB0Ymw9"
    "ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoImgyaC10YWJsZSIpOwogIGlmKCFpbnB8fCF0YmwpcmV0"
    "dXJuOwogIGlucC5hZGRFdmVudExpc3RlbmVyKCJpbnB1dCIsZnVuY3Rpb24oKXsKICAgIHZhciBx"
    "PXRoaXMudmFsdWUudHJpbSgpLnRvTG93ZXJDYXNlKCk7CiAgICB2YXIgcm93cz10YmwudEJvZGll"
    "c1swXS5yb3dzOwogICAgZm9yKHZhciBpPTA7aTxyb3dzLmxlbmd0aDtpKyspewogICAgICB2YXIg"
    "bT0ocm93c1tpXS5jZWxsc1swXT9yb3dzW2ldLmNlbGxzWzBdLnRleHRDb250ZW50OiIiKS50b0xv"
    "d2VyQ2FzZSgpOwogICAgICB2YXIgbz0ocm93c1tpXS5jZWxsc1sxXT9yb3dzW2ldLmNlbGxzWzFd"
    "LnRleHRDb250ZW50OiIiKS50b0xvd2VyQ2FzZSgpOwogICAgICByb3dzW2ldLnN0eWxlLmRpc3Bs"
    "YXk9KCFxfHxtLmluZGV4T2YocSk+LTF8fG8uaW5kZXhPZihxKT4tMSk/IiI6Im5vbmUiOwogICAg"
    "fQogIH0pOwp9KSgpOwo8L3NjcmlwdD4K"
)

js = base64.b64decode(B).decode("utf-8")
p = pathlib.Path("docs/hof/rivalries.html")
html = p.read_text(encoding="utf-8")
if "FDH_H2H" not in html:
    print("ERROR: run generate_site.py first")
elif 'getElementById("mgr-a")' in html:
    print("Already patched")
else:
    out = html.replace("</body>", js + "</body>", 1)
    p.write_text(out, encoding="utf-8")
    print("Done:", p.stat().st_size, "bytes")
    print('Next: git add -A && git commit -m "add H2H lookup JS" && git push')
