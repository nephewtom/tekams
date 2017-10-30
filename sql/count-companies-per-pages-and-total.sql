.echo on
select page, count(page) as c from company group by page having c>1 union all select 'SUM' page, count(page) from company;
select count(*) from company;
.echo off
