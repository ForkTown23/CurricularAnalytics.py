# file: DegreePlanCreation.jl

from typing import List, Literal, Optional, Protocol, Union

from src.DataTypes.Course import AbstractCourse, Course
from src.DataTypes.Curriculum import Curriculum
from src.DataTypes.DataTypes import pre, strict_co
from src.DataTypes.DegreePlan import DegreePlan, Term


class CreateTerms(Protocol):
    def __call__(
        self,
        curric: Curriculum,
        additional_courses: List[AbstractCourse] = [],
        min_terms: int = 2,
        max_terms: int = 10,
        min_cpt: int = 3,
        max_cpt: int = 19,
    ) -> Union[List[Term], Literal[False]]:
        ...


def bin_filling(
    curric: Curriculum,
    additional_courses: List[AbstractCourse] = [],
    min_terms: int = 2,
    max_terms: int = 10,
    min_cpt: int = 3,
    max_cpt: int = 19,
) -> Union[List[Term], Literal[False]]:
    terms: List[Term] = []
    term_credits = 0
    term_courses: List[AbstractCourse] = []
    UC = curric.courses.copy()  # lower numbered courses will be considered first
    UC.sort(key=course_num)
    while len(UC) > 0:
        c = select_vertex(curric, term_courses, UC)
        if (c) != None:
            UC.remove(c)
            if term_credits + c.credit_hours <= max_cpt:
                term_courses.append(c)
                term_credits = term_credits + c.credit_hours
            else:  # exceeded max credits allowed per term
                terms.append(Term(term_courses))
                term_courses = [c]
                term_credits = c.credit_hours
            # if c serves as a strict-corequisite for other courses, include them in current term too
            for course in UC:
                for req in course.requisites.items():
                    if req[0] == c.id:
                        if req[1] == strict_co:
                            UC.remove(course)
                            term_courses.append(course)
                            term_credits = term_credits + course.credit_hours
        else:  # can't find a course to add to current term, create a new term
            if len(term_courses) > 0:
                terms.append(Term(term_courses))
            term_courses = []
            term_credits = 0
    if len(term_courses) > 0:
        terms.append(Term(term_courses))
    return terms


def create_degree_plan(
    curric: Curriculum,
    create_terms: CreateTerms = bin_filling,
    name: str = "",
    additional_courses: List[AbstractCourse] = [],
    min_terms: int = 1,
    max_terms: int = 10,
    min_cpt: int = 3,
    max_cpt: int = 19,
) -> Optional[DegreePlan]:
    terms = create_terms(
        curric,
        additional_courses,
        min_terms=min_terms,
        max_terms=max_terms,
        min_cpt=min_cpt,
        max_cpt=max_cpt,
    )
    if terms == False:
        print("Unable to create degree plan")
        return
    else:
        return DegreePlan(name, curric, terms)


def select_vertex(
    curric: Curriculum, term_courses: List[AbstractCourse], UC: List[AbstractCourse]
):
    for target in UC:
        t_id = target.vertex_id[curric.id]
        UCs = UC.copy()
        UCs = [c for c in UCs if c.id != target.id]
        invariant1 = True
        for source in UCs:
            s_id = source.vertex_id[curric.id]
            vlist = reachable_from(curric.graph, s_id)
            if t_id in vlist:  # target cannot be moved to AC
                invariant1 = False  # invariant 1 violated
                break  # try a new target
        if invariant1 == True:
            invariant2 = True
            for c in term_courses:
                if (
                    c.id in target.requisites and target.requisites[c.id] == pre
                ):  # AND shortcircuits, otherwise 2nd expression would error
                    invariant2 = False
                    break  # try a new target
            if invariant2 == True:
                return target
    return None


def course_num(c: Course) -> str:
    return c.num if c.num != "" else c.name
