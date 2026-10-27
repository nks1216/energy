**Evaluating Temperature Sensitivity and Structural Growth in ERCOT Electricity Demand (2021–2025)**


$$
\ln(\text{Load}_t) = \beta_1 \text{CDD}_t + \beta_2 \text{HDD}_t + \gamma \cdot \text{Trend}_t + \text{Month/Day/Hour FE} + \varepsilon_t
$$


To capture the weather-driven component of the system-wide load, we construct a population-weighted temperature index based on the four major metropolitan statistical areas (MSAs)—Dallas, Houston, San Antonio, and Austin—which account for the vast majority of Texas's population and aggregated electricity consumption.

Population weights are derived from the U.S. Census Bureau Annual Metropolitan Area Resident Population Estimates for Dallas-Fort Worth, Houston, San Antonio, and Austin MSAs, retrieved via FRED (Federal Reserve Economic Data). A fixed average share across the 2021–2025 sample period is applied to construct the population-weighted statewide weather indices.

**< Data >**

**ERCOT**

Home > Grid Information > Load > Hourly Load Data Archives

[www.ercot.com/gridinfo/load/load_hist](https://www.ercot.com/gridinfo/load/load_hist)

[2021 ERCOT Hourly Load Data](https://www.ercot.com/files/docs/2021/11/12/Native_Load_2021.zip "2021 ERCOT Hourly Load Data") ~ [2025 ERCOT Hourly Load Data](https://www.ercot.com/files/docs/2025/02/11/Native_Load_2025.zip "2025 ERCOT Hourly Load Data")

**NOAA**

Local Climatological Data V2

[www.ncei.noaa.gov](https://www.ncei.noaa.gov/)

| city                  | airport | station name                           | GHCN ID               |
| --------------------- | ------- | -------------------------------------- | --------------------- |
| **Austin**      | AUS     | AUSTIN BERGSTROM INTERNATIONAL AIRPORT | **USW00013904** |
| **Dallas**      | DFW     | DAL FTW WSCMO AIRPORT                  | **USW00003927** |
| **Houston**     | IAH     | HOUSTON INTERCONTINENTAL AIRPORT       | **USW00012960** |
| **San Antonio** | SAT     | SAN ANTONIO INTERNATIONAL AIRPORT      | **USW00012921** |

**Population**

FRED (Federal Reserve Economic Data)

[fred.stlouisfed.org/series/AUSPOP](https://fred.stlouisfed.org/series/AUSPOP)

[Home](https://fred.stlouisfed.org/)>[Categories](https://fred.stlouisfed.org/categories)>[U.S. Regional Data](https://fred.stlouisfed.org/categories/3008)>[States](https://fred.stlouisfed.org/categories/27281)>[Texas](https://fred.stlouisfed.org/categories/27326)>[MSAs](https://fred.stlouisfed.org/categories/30907)>[Austin-Round Rock-San Marcos, TX](https://fred.stlouisfed.org/categories/30910)

* **Dallas-Fort Worth MSA** :`DFWPOP`
* **Houston MSA** :`HTNPOP`
* **San Antonio MSA** :`SATPOP`
* **Austin MSA** :`AUSPOP`
