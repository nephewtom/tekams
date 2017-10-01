select conns.uid, ranking, name, url from company inner join conns on conns.uid = company.uid where phone = 'none';
