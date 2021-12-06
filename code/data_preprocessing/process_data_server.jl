using JSON3
using JLD2
using DFControl
using Dates

for sys in filter(isdir, readdir()) # Structure
    results = []
    @info "Processing $sys."
    datfile = joinpath(sys, "data.json")
    ispath(datfile) && rm(datfile)
    for d1 in readdir(sys)
        ecutwfc = parse(Int, d1)
        dir1 = joinpath(sys, d1)
        for d2 in readdir(dir1)
            ecutrho = parse(Int, d2)
            dir2 = joinpath(dir1, d2)
            for d3 in readdir(dir2)
                nk = parse(Int, d3)
                dir3 = joinpath(dir2, d3)
                resfile = joinpath(dir3, "results.jld2")
                if ispath(resfile)
                    @show resfile
                    outdata = JLD2.load(resfile)["outputdata"]["scf"]
                    if haskey(outdata, :accuracy) && haskey(outdata, :fermi) && haskey(outdata, :timing)
                        outd = Dict("k_density" => 1/nk, "ecutrho" => ecutrho, "ecutwfc" => ecutwfc)
                        
                        outd["accuracy"]=outdata[:accuracy][end]
                        outd["total_energy"]=outdata[:total_energy][end]/2
                        outd["n_iterations"] = outdata[:scf_iteration][end]
                        outd["converged"] = outdata[:converged]
                        outd["fermi"] = outdata[:fermi]
                        outd["time"] = Dates.toms(outdata[:timing][1].wall + outdata[:timing][2].wall)
                        push!(results, outd)
                    end
                end
            end
        end
    end
    @show length(results)
    !isempty(results) && JSON3.write(datfile, results)
end