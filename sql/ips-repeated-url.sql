select uid, ip, url from conns where url in (select conns.url from company join conns on conns.uid = company.uid where name = 'none') order by url;
