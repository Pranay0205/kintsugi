# Case Studies: V3 LLM vs Human Annotation Agreement

**Dataset:** 10 struggling students, 372 problems, 6,696 binary KC decisions

## Case A: All Three Raters Share a Gap - V3 Works

**Student 10155, Problem 22** | Score: 0.36

**Required KCs:** DefFunction, If/Else, LogicAndNotOr, LogicCompareNum, Math+-*/, NestedIf

**Problem:** Write two methods in Java that implements the following logic: Given 3 int values, a, b, and c, return their sum. However, if any of the values is a teen--in the range 13..19 inclusive--then that value counts as 0, except 15 and 16 do not count as teens. Write a separate helper method called fixTeen() that takes in an int value and returns that value fixed for the teen rule. In this way you avoid repeating the teen code 3 times (i.e. "decomposition").

**Student Code:**

```java
public int noTeenSum(int a, int b, int c)
{
    int sum = a+b+c;
    return sum;
}

public int fixTeen(int n)
{
    if (n>=13 && n<14)
    {
        return 0;
    }
    
    if (n>=17 && n<19)
    {
     	return 0;   
    }
    
    return 0;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | DefFunction, LogicAndNotOr, LogicCompareNum |
| Human B (Arundhati) | DefFunction, LogicAndNotOr, LogicCompareNum |
| LLM V3 | DefFunction, LogicAndNotOr, LogicCompareNum |

**Shared by all three:** DefFunction, LogicAndNotOr, LogicCompareNum

**Analysis:** [TODO: Write narrative for thesis]

---

## Case B: Humans Agree, LLM Diverges - V3 Fails

**Student 10155, Problem 40** | Score: 0.153846

**Required KCs:** For, If/Else, LogicAndNotOr, LogicCompareNum, StringEqual, StringFormat, StringIndex

**Problem:** A sandwich is two pieces of bread with something in between. Write a Java method that takes in a string str and returns the string that is between the first and last appearance of "bread" in str. Return the empty string "" if there are not two pieces of bread.

**Student Code:**

```java
public String getSandwich(String str)
{
  	if (str.startsWith("bread"))
    {
        return "";
    }
    
    
    return str;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | For, StringEqual, StringFormat |
| Human B (Arundhati) | For, StringEqual, StringFormat |
| LLM V3 | If/Else, StringEqual, StringIndex |

**Analysis:** [TODO: Write narrative for thesis]

---

## Case C: LLM Agrees With One Human - V3 Within Human Variance

**Student 14374, Problem 38** | Score: 0.733333

**Required KCs:** CharEqual, For, If/Else, LogicAndNotOr, StringEqual, StringFormat, StringIndex

**Problem:** Write a function in Java that returns true if the given string str contains an occurrence of the substring "xyz" where "xyz" is not directly preceded by a period ("."). For example, "xxyz" counts, while "x.xyz" does not.

**Student Code:**

```java
public boolean xyzThere(String str)
{
     if (str.contains("xyz"))
     {
         return true;
     }
    return false;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | CharEqual, LogicAndNotOr, StringIndex |
| Human B (Arundhati) | LogicAndNotOr, StringConcat, StringEqual |
| LLM V3 | CharEqual, LogicAndNotOr, StringIndex |

**Analysis:** [TODO: Write narrative for thesis]

---

## Case D: LLM Finds Unique Insight - V3 Adds Value

**Student 10155, Problem 40** | Score: 0.153846

**Required KCs:** For, If/Else, LogicAndNotOr, LogicCompareNum, StringEqual, StringFormat, StringIndex

**Problem:** A sandwich is two pieces of bread with something in between. Write a Java method that takes in a string str and returns the string that is between the first and last appearance of "bread" in str. Return the empty string "" if there are not two pieces of bread.

**Student Code:**

```java
public String getSandwich(String str)
{
  	if (str.startsWith("bread"))
    {
        return "";
    }
    
    
    return str;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | For, StringEqual, StringFormat |
| Human B (Arundhati) | For, StringEqual, StringFormat |
| LLM V3 | If/Else, StringEqual, StringIndex |

**LLM-only tags:** If/Else, StringIndex

**Analysis:** [TODO: Write narrative for thesis]

---

