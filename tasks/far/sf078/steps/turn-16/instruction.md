And here, Any reason not to use attrs? Saying "I already put in all this work" is fair, but it seems like with the dataclass callout that attrs would also be a really good fit here.

Actually, I just realized that the function is a generator on purpose to allow for short-circuiting in case people only need part of the results. So the question is whether you would rather be able to memoize the results or allow short-circuiting?

Can we add a comment so we don't forget why that is the case in the future?