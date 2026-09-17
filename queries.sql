-- sites
SELECT DISTINCT LaunchSite FROM launches ORDER BY LaunchSite;

-- cape_examples
SELECT Date, LaunchSite FROM launches WHERE LaunchSite LIKE 'CC%' LIMIT 5;

-- nasa_payload
SELECT COUNT(*) AS launches, SUM(PayloadMass) AS known_payload_kg, COUNT(PayloadMass) AS known_mass_count FROM launches WHERE Customer LIKE '%NASA%';

-- v11_payload
SELECT COUNT(*) AS launches, AVG(PayloadMass) AS mean_known_payload_kg FROM launches WHERE BoosterVersion LIKE '%v1.1%';

-- first_ground_success
SELECT MIN(Date) AS first_date FROM launches WHERE LandingOutcome LIKE 'Success%ground pad%';

-- drone_4_to_6_tonnes
SELECT Date, BoosterVersion, PayloadMass FROM launches WHERE LandingOutcome LIKE 'Success%drone ship%' AND PayloadMass > 4000 AND PayloadMass < 6000 ORDER BY Date;

-- mission_outcomes
SELECT MissionOutcome, COUNT(*) AS launches FROM launches GROUP BY MissionOutcome ORDER BY launches DESC;

-- landing_outcomes
SELECT LandingOutcome, COUNT(*) AS launches FROM launches GROUP BY LandingOutcome ORDER BY launches DESC;

-- max_payload
SELECT Date, BoosterVersion, PayloadMass FROM launches WHERE PayloadMass=(SELECT MAX(PayloadMass) FROM launches) ORDER BY Date;

-- 2015_drone_failures
SELECT strftime('%m',Date) AS month, BoosterVersion, LaunchSite FROM launches WHERE Date LIKE '2015%' AND LandingOutcome LIKE 'Failure%drone ship%';

-- historical_outcome_rank
SELECT LandingOutcome, COUNT(*) AS launches FROM launches WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' GROUP BY LandingOutcome ORDER BY launches DESC;

-- site_success
SELECT LaunchSite,COUNT(*) AS launches,SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END) AS recovered,ROUND(100.0*SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END)/COUNT(*),1) AS recovered_pct FROM launches GROUP BY LaunchSite ORDER BY recovered_pct DESC;

-- normalized_site_success
SELECT SiteGroup,COUNT(*) AS launches,SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END) AS recovered,ROUND(100.0*SUM(CASE WHEN LandingOutcome LIKE 'Success%' THEN 1 ELSE 0 END)/COUNT(*),1) AS recovered_pct FROM launches GROUP BY SiteGroup ORDER BY recovered_pct DESC;