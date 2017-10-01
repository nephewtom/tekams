select * from conns where url in (select url from conns group by url having count(*) > 1);
