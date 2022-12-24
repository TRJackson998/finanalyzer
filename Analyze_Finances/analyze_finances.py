"""
Title:
    Analyze Finances

Author:
    Terrence Jackson

Source:
    Banking Apps don't categorize transactions very accurately,
    so if they do any kind of representation of your spending, it often isn't useful.

Summary:
    Given a csv of banking data saved to the Assets folder, 
    creates your personal category mappings (with your input), 
    and generates a pie chart of your spending

Additional Details:
    Planned updates: create a gui for user input about what graph they want to see
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from Assets.category_mappings import category_mappings
from generate_mappings import generate_mappings


class Time:
    """Parent class"""

    __df: pd.DataFrame

    def __init__(self, df: pd.DataFrame) -> None:
        self.__df = df

    def visualize_all(self):
        summ_dict = {}
        for category in self.__df["Category"].unique():
            category_df = self.__df[self.__df["Category"] == category]
            summation = category_df["Amount"].sum()
            summ_dict[category] = summation
        aggregated_df = pd.DataFrame.from_dict(
            summ_dict, orient="index", columns=["Sum"]
        )
        aggregated_df["Sum"] = aggregated_df["Sum"].apply(lambda x: abs(x))
        aggregated_df = aggregated_df[aggregated_df["Sum"] > 1.0]

        return aggregated_df

    def visualize_costs(self):
        df = self.visualize_all()
        df = df.drop(index="Income")
        return df

    def visualize(self, all: bool = True, just_costs: bool = False):
        if all & (~just_costs):
            aggregated_df = self.visualize_all()
        else:
            aggregated_df = self.visualize_costs()

        plt.pie(
            aggregated_df["Sum"],
            labels=aggregated_df.index,
            autopct="%1.1f%%",
            radius=1.5,
            rotatelabels=True,
        )
        plt.show()


class Day(Time):
    __df: pd.DataFrame

    def __init__(self, day: date, df: pd.DataFrame) -> None:
        self.__df = df
        super().__init__(df)


class Week(Time):
    __df: pd.DataFrame
    __days: list[Day]

    def __init__(self, monday: date, df: pd.DataFrame) -> None:
        self.__df = df
        super().__init__(df)
        self.__days = []  # 7

        while monday.weekday() != 0:
            monday = monday - timedelta(days=1)

        tuesday = monday + timedelta(days=1)
        wednesday = monday + timedelta(days=2)
        thursday = monday + timedelta(days=3)
        friday = monday + timedelta(days=4)
        saturday = monday + timedelta(days=5)
        sunday = monday + timedelta(days=6)

        week = [monday, tuesday, wednesday, thursday, friday, saturday, sunday]

        for i in range(7):
            mask = self.__df["Date"] == week[i]
            self.__days.append(Day(week[i], self.__df[mask]))


class Month(Time):
    __weeks: list[Week]
    __month_of_year: int
    __df: pd.DataFrame

    def __init__(self, first: date, df: pd.DataFrame) -> None:
        self.__df = df
        super().__init__(df)
        self.__weeks = []  # 5
        self.__month_of_year = first.month

        while first.day != 1:
            first = first - timedelta(days=1)

        last = first
        while last.weekday() != 6:
            last = last + timedelta(days=1)

        i = 0
        while (first.month == self.__month_of_year) & (first.day < 32):
            mask = (
                self.__df["Date"]
                >= pd.to_datetime(f"{first.year}-{first.month}-{first.day}")
            ) & (
                self.__df["Date"]
                <= pd.to_datetime(f"{last.year}-{last.month}-{last.day}")
            )
            self.__weeks.append(Week(first, self.__df[mask]))
            first = last + timedelta(days=1)
            last = first + timedelta(days=7)
            if last.day > (last + relativedelta(day=31)).day:
                last = last + relativedelta(day=31)
            i += 1


class Year(Time):
    months: list[Month]
    __df: pd.DataFrame

    def __init__(self, year: int, df: pd.DataFrame) -> None:
        self.__df = df
        super().__init__(df)

        self.months = []  # 13. skipping 0 for ease of understanding. 1 = Jan etc
        self.__df["Month"] = self.__df["Date"].apply(lambda x: x.month)
        for i in range(13):
            if i == 0:
                self.months.append(0)
            else:
                mask = self.__df["Month"] == i
                self.months.append(
                    Month(date(year=year, month=i, day=1), self.__df[mask])
                )


def read_csv(name: str) -> pd.DataFrame:
    """
    Reads csv, cleans dates, recategorizes, removes internal transfers


    Args:
        str name: name of csv to read
    Returns:
        DataFrame with usable dates
    """
    df = pd.read_csv(os.path.join(".\\Analyze_Finances", "Assets", name))

    # clean dates
    df["Date"] = pd.to_datetime(df["Date"])

    # recategorize
    df["Category"] = df["Description"].apply(lambda x: recategorize(x))

    # remove internal transfers
    df = df[df["Category"] != "Internal Transfer"]

    return df


def recategorize(x) -> pd.DataFrame:
    """Helper function, matches transactions up to user category mappings"""
    for key in category_mappings.keys():
        if x in category_mappings[key]:
            return key


def main():
    """Runtime function"""
    generate_mappings()
    df = read_csv("test.csv")
    tt = Year(2022, df)
    tt.visualize(just_costs=True)
    may = tt.months[5]
    may.visualize()


if __name__ == "__main__":
    main()
