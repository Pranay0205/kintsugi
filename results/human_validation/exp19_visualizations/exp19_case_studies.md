# Case Studies: V3 LLM vs Human Annotation Agreement

**Dataset:** 10 struggling students, 372 problems, 6,696 binary KC decisions

## Case A: All Three Raters Share a Gap - V3 Works

**Student 9948, Problem 22** | Score: 0.36

**Required KCs:** DefFunction, If/Else, LogicAndNotOr, LogicCompareNum, Math+-*/, NestedIf

**Problem:** Write two methods in Java that implements the following logic: Given 3 int values, a, b, and c, return their sum. However, if any of the values is a teen--in the range 13..19 inclusive--then that value counts as 0, except 15 and 16 do not count as teens. Write a separate helper method called fixTeen() that takes in an int value and returns that value fixed for the teen rule. In this way you avoid repeating the teen code 3 times (i.e. "decomposition").

**Student Code:**

```java
public int noTeenSum(int a, int b, int c)
{
	return a + b + c;
}

public int fixTeen(int n)
{
    if(n > 12 && n < 20)
        return 0;
    if(n == 15 && n == 16)
        return n;
    return 0;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | DefFunction, If/Else, LogicAndNotOr, NestedIf |
| Human B (Arundhati) | LogicAndNotOr, LogicCompareNum |
| LLM V3 | DefFunction, LogicAndNotOr, LogicCompareNum |

**Shared by all three:** LogicAndNotOr

**Analysis:** [TODO: Write narrative for thesis]

---

## Case B: Humans Agree, LLM Diverges - V3 Fails

**Student 10155, Problem 24** | Score: 0.590909

**Required KCs:** If/Else, LogicAndNotOr, LogicCompareNum, Math+-*/

**Problem:** Write a function in Java that implements the following logic: Given 2 int values greater than 0, return whichever value is nearest to 21 without going over. Return 0 if they both go over.

**Student Code:**

```java
public int blackjack(int a, int b)
{
    if (b-a > 0)
    {
    	return b;
    }
    
    else if (b-a<0)
    {
        return a;
    }
    
    else if (a-b<0)
    {
        return b;
    }
    
    else if (a-b>0)
    {
        return a;
    }
    
    else if (a>21 && b>21)
    {
        return 0;
    }
    
    
    
    return 0;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | LogicAndNotOr, LogicCompareNum, Math+-*/ |
| Human B (Arundhati) | LogicAndNotOr, LogicCompareNum, Math+-*/ |
| LLM V3 | If/Else, LogicCompareNum |

**Analysis:** [TODO: Write narrative for thesis]

---

## Case C: LLM Agrees With One Human - V3 Within Human Variance

**Student 14189, Problem 24** | Score: 0.8636360000000001

**Required KCs:** If/Else, LogicAndNotOr, LogicCompareNum, Math+-*/

**Problem:** Write a function in Java that implements the following logic: Given 2 int values greater than 0, return whichever value is nearest to 21 without going over. Return 0 if they both go over.

**Student Code:**

```java
public int blackjack(int a, int b)
{
    if (a > 21 && b > 21)
        return 0;
    else if (a > b && a < 21)
        return a;
    else if (b > a && b < 21)
        return b;
    return a;
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | If/Else, LogicCompareNum, Math+-*/ |
| Human B (Arundhati) | LogicAndNotOr, LogicCompareNum |
| LLM V3 | LogicAndNotOr, LogicCompareNum |

**Analysis:** [TODO: Write narrative for thesis]

---

## Case D: LLM Finds Unique Insight - V3 Adds Value

**Student 10155, Problem 37** | Score: 0.666667

**Required KCs:** If/Else, LogicCompareNum, StringEqual, StringFormat, StringIndex, StringLen

**Problem:** Given two strings, return true if either of the strings appears at the very end of the other string, ignoring upper/lower case differences (in other words, the computation should not be "case sensitive"). Note: str.toLowerCase() returns the lowercase version of a string.

**Student Code:**

```java
public boolean endOther(String a, String b)
{
 	if (b.contains(a.substring(0)))
        {
            return true;
        }
    
    return false;
    
}
```

| Rater | Tagged Gaps |
|---|---|
| Human A (Pranay) | LogicCompareNum, StringIndex, StringLen |
| Human B (Arundhati) | (none) |
| LLM V3 | LogicAndNotOr, StringEqual |

**LLM-only tags:** LogicAndNotOr, StringEqual

**Analysis:** [TODO: Write narrative for thesis]

---

