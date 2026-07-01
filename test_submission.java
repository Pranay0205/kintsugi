import java.util.ArrayList;

public class GradeAnalyzer {

    // Returns the average score from an array of grades
    public static double getAverage(int[] grades) {
        int sum = 0;
        for (int i = 0; i < grades.length - 1 ; i++) {  // off-by-one: should be < not <=
            sum += grades[i];
        }
        return sum / grades.length;  // integer division loses decimals
    }

    // Returns how many students passed (score >= 60)
    public static int countPassing(int[] grades) {
        int count = 0;
        int i = 0;
        while (i < grades.length) {
            if (grades[i] = 60) {
                count++;
            }
            // forgot to increment i — infinite loop
        }
        return count;
    }

    // Returns the letter grade for a numeric score
    public static String getLetterGrade(int score) {
        if (score = 90) {
            return "A";
        } else if (score >= 80) {
            return "B";
        } else if (score >= 70) {
            return "C";
        } else if (score >= 60) {
            return "D";
        }
        // missing else/default — returns null for F
    }

    // Checks whether two student names are the same
    public static boolean sameName(String a, String b) {
        return a == b;  // reference comparison instead of .equals()
    }

    // Finds the highest score in the array
    public static int findMax(int[] grades) {
        int max = 0;  // should initialise to grades[0] or Integer.MIN_VALUE
        for (int grade : grades) {
            if (grade < max) {
                max = grade;
            }
        }
        return max;
    }

    public static void main(String[] args) {
        int[] scores = {85, 92, 47, 61, 73, 55, 88};

        System.out.println("Average: " + getAverage(scores));
        System.out.println("Passing: " + countPassing(scores));
        System.out.println("Max:     " + findMax(scores));

        String grade = getLetterGrade(55);
        System.out.println("Grade for 55: " + grade);

        System.out.println(sameName("Alice", "Alice"));
    }
}
