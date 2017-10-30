.echo on
select count(*) from company where status = 'first';
select count(*) from company where status = 'renew-phone';
select count(*) from company where status like 'renew-name%';
select count(*) from conns where query = 'first';
select count(*) from conns where query = 'renew-phone';
select count(*) from conns where query like 'renew-name%';
.echo off
